"""PM2 orchestrator. Ranking/context only — no orders, no sizing, no QRF."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from botmoduleproject1.adapters.market.synthetic import SyntheticMarketFeed
from botmoduleproject1.app.capabilities import ModuleMetadata
from botmoduleproject1.app.health import CheckKind, CheckResult
from botmoduleproject1.contracts.v1.market import OhlcvBar, Timeframe
from botmoduleproject1.contracts.v1.pm2 import (
    CandidateContextSnapshot,
    PublicationBundle,
    RankedCandidate,
)
from botmoduleproject1.modules.pm2_market_context.capabilities import PM2_METADATA
from botmoduleproject1.modules.pm2_market_context.config.schema import Pm2Config, config_from_settings
from botmoduleproject1.modules.pm2_market_context.diagnostics.health import health_checks as pm2_health
from botmoduleproject1.modules.pm2_market_context.diagnostics.quality_checks import quality_summary
from botmoduleproject1.modules.pm2_market_context.diagnostics.readiness import publication_allowed
from botmoduleproject1.modules.pm2_market_context.domain.ids import candidate_id
from botmoduleproject1.modules.pm2_market_context.engines.bias_engine import evaluate_bias
from botmoduleproject1.modules.pm2_market_context.engines.correlation_engine import view_for
from botmoduleproject1.modules.pm2_market_context.engines.momentum_engine import evaluate_momentum
from botmoduleproject1.modules.pm2_market_context.engines.session_liquidity_engine import evaluate_session
from botmoduleproject1.modules.pm2_market_context.engines.structure_engine import evaluate_structure
from botmoduleproject1.modules.pm2_market_context.engines.volatility_engine import evaluate_volatility
from botmoduleproject1.modules.pm2_market_context.features.builder import build_snapshot
from botmoduleproject1.modules.pm2_market_context.features.normalization import assert_no_lookahead
from botmoduleproject1.modules.pm2_market_context.publication.handoff_gateway import stamp_handoff
from botmoduleproject1.modules.pm2_market_context.publication.publisher import publish, scan_correlation_id
from botmoduleproject1.modules.pm2_market_context.qualification.state_machine import initial, transition
from botmoduleproject1.modules.pm2_market_context.ranking.deterministic_ranker import DeterministicRanker
from botmoduleproject1.modules.pm2_market_context.regime.regime_engine import RegimeEngine
from botmoduleproject1.modules.pm2_market_context.scanner.universe_scanner import SymbolSnapshot, UniverseScanner
from botmoduleproject1.modules.pm2_market_context.scoring.confluence_engine import score as score_confluence
from botmoduleproject1.modules.pm2_market_context.scoring.vetoes import vetoes as collect_vetoes
from botmoduleproject1.modules.pm2_market_context.suppression.conflict_suppressor import suppress
from botmoduleproject1.modules.pm2_market_context.telemetry.attribution import attribute_all
from botmoduleproject1.modules.pm2_market_context.telemetry.calibration import calibration_snapshot
from botmoduleproject1.modules.pm2_market_context.telemetry.degradation import degradation_alerts
from botmoduleproject1.modules.pm2_market_context.telemetry.ghost_tracking import ghost_records
from botmoduleproject1.modules.pm2_market_context.telemetry.metrics import Pm2Metrics


def _side_bias(long_score: float, short_score: float) -> str:
    if long_score > short_score + 5:
        return "long"
    if short_score > long_score + 5:
        return "short"
    return "flat"


class PM2Module:
    """Market intelligence module. Implements MarketDataProvider + scan()."""

    def __init__(
        self,
        config: Pm2Config,
        clock: Any,
        feed: SyntheticMarketFeed | None = None,
    ) -> None:
        self.config = config
        self.clock = clock
        as_of = clock.now()
        self.feed = feed or SyntheticMarketFeed(as_of=as_of, lookback=config.lookback_bars)
        self.scanner = UniverseScanner(config, self.feed)
        self.regime = RegimeEngine(hold=config.thresholds.persistence_bars)
        self.ranker = DeterministicRanker()
        self._states: dict[str, Any] = {}
        self._last_bundle: PublicationBundle | None = None
        self._last_qualities: tuple = ()
        self._last_attribution: tuple[dict[str, object], ...] = ()
        self.metrics = Pm2Metrics()

    @classmethod
    def from_settings(cls, settings: object, clock: Any) -> PM2Module:
        return cls(config_from_settings(settings), clock)

    def metadata(self) -> ModuleMetadata:
        return PM2_METADATA

    def latest_bar(self, symbol: str, timeframe: Timeframe) -> OhlcvBar | None:
        return self.feed.latest_bar(symbol, timeframe)

    def health_checks(self, kind: CheckKind) -> list[CheckResult]:
        return pm2_health(
            kind,
            enabled=True,
            last_bundle=self._last_bundle,
            last_qualities=self._last_qualities,
        )

    def last_bundle(self) -> PublicationBundle | None:
        return self._last_bundle

    def scan(self, as_of: datetime | None = None) -> PublicationBundle:
        as_of = as_of or self.clock.now()
        self.feed = SyntheticMarketFeed(as_of=as_of, lookback=self.config.lookback_bars)
        self.scanner = UniverseScanner(self.config, self.feed)
        snapshots = self.scanner.scan(as_of)
        self._last_qualities = tuple(s.quality for s in snapshots)
        allow_pub = publication_allowed(self._last_qualities)

        drafted: list[RankedCandidate] = []
        for snap in snapshots:
            drafted.append(self._evaluate_symbol(snap, as_of))

        ranked = self.ranker.rank(tuple(drafted), as_of=as_of, config=self.config)
        ranked, suppressed = suppress(ranked, self.config)
        ranked = self.ranker.rank(ranked, as_of=as_of, config=self.config)
        ranked = stamp_handoff(ranked, self.config)

        if not allow_pub:
            ranked = tuple(
                item.model_copy(update={"handoff_eligibility": False}) for item in ranked
            )

        attrib = attribute_all(ranked) if self.config.telemetry else ()
        calib = calibration_snapshot(ranked)
        alerts = degradation_alerts(ranked, qualities=self._last_qualities)
        diagnostics = {
            "operating_mode": self.config.operating_mode.value,
            "ranking_mode": self.config.ranking_mode.value,
            "publication_allowed": allow_pub,
            "quality": quality_summary(snapshots),
            "degradation_alerts": list(alerts),
            "hmm_adapter": False,
            "gmm_adapter": False,
            "orders": False,
            "qrf": False,
        }
        health = {
            "freshness_ok": allow_pub,
            "watchlist_only": not allow_pub or bool(alerts),
        }
        bundle = publish(
            ranked,
            suppressed,
            as_of=as_of,
            config=self.config,
            diagnostics=diagnostics,
            health=health,
            calibration=calib,
        )
        if self.config.ghost_tracking:
            ghosts = ghost_records(ranked, bundle)
            bundle = bundle.model_copy(
                update={
                    "diagnostics_summary": {
                        **bundle.diagnostics_summary,
                        "ghosts": list(ghosts),
                    }
                }
            )
        if not allow_pub:
            bundle = bundle.model_copy(update={"shortlist": ()})
        self._last_bundle = bundle
        self._last_attribution = attrib
        self.metrics.record_scan(
            shortlist=len(bundle.shortlist),
            suppressed=len(bundle.suppressed),
            vetoes=sum(len(c.scorecard.vetoes) for c in ranked),
        )
        return bundle

    def _evaluate_symbol(self, snap: SymbolSnapshot, as_of: datetime) -> RankedCandidate:
        decision_tf = Timeframe(self.config.decision_timeframe)
        features: dict = {}
        for raw_tf, bars in snap.bars_by_tf.items():
            tf = Timeframe(raw_tf)
            assert_no_lookahead(bars, as_of.timestamp())
            features[raw_tf] = build_snapshot(snap.symbol, tf, bars, as_of)
        decision_bars = snap.bars_by_tf.get(self.config.decision_timeframe, ())
        decision_feat = features.get(self.config.decision_timeframe) or build_snapshot(
            snap.symbol, decision_tf, decision_bars, as_of
        )
        regime_state, _label = self.regime.evaluate(decision_feat, as_of)
        bias = evaluate_bias(features)
        structure = evaluate_structure(decision_bars)
        momentum = evaluate_momentum(decision_feat)
        volatility = evaluate_volatility(decision_feat)
        weekend = as_of.weekday() >= 5
        session = evaluate_session(as_of, is_weekend=weekend)
        veto_list = collect_vetoes(
            quality=snap.quality,
            regime=regime_state.regime,
            phase=volatility.phase,
            rollover=session.rollover_risk,
            weekend=weekend,
        )
        scorecard = score_confluence(
            config=self.config,
            regime=regime_state.regime,
            regime_confidence=regime_state.confidence,
            bias=bias,
            structure=structure,
            momentum=momentum,
            volatility=volatility,
            session=session,
            veto_list=veto_list,
            quality=snap.quality,
        )
        prev = self._states.get(snap.symbol) or initial(as_of)
        stale = False
        if prev.stale_after is not None and as_of >= prev.stale_after:
            stale = True
        state = transition(prev, scorecard, as_of, self.config.thresholds, stale=stale)
        self._states[snap.symbol] = state
        cid = candidate_id(snap.symbol, as_of)
        corr = scan_correlation_id(as_of)
        cluster = view_for(snap.symbol).cluster
        family_summary = {
            "regime": scorecard.regime_score,
            "directional_bias": max(scorecard.long_score, scorecard.short_score),
            "structure": scorecard.structure_score,
            "momentum": scorecard.momentum_score,
            "volatility": scorecard.volatility_score,
            "session_liquidity": scorecard.session_score,
        }
        context = CandidateContextSnapshot(
            candidate_id=cid,
            event_id=cid,
            correlation_id=corr,
            symbol=snap.symbol,
            as_of=as_of,
            timeframes=tuple(snap.bars_by_tf.keys()),
            regime=regime_state.regime,
            regime_confidence=regime_state.confidence,
            sessions=session.context.sessions,
            session_quality=session.context.quality,
            data_quality=snap.quality,
            feature_family_summary=family_summary,
            feature_set_version=self.config.feature_set_version,
        )
        timing = as_of + timedelta(hours=max(1, self.config.thresholds.stale_bars))
        return RankedCandidate(
            candidate_id=cid,
            event_id=cid,
            correlation_id=corr,
            causation_id=corr,
            symbol=snap.symbol,
            as_of=as_of,
            final_rank=1,
            scorecard=scorecard,
            state=state,
            context=context,
            correlation_cluster=cluster,
            handoff_eligibility=False,
            side_bias=_side_bias(scorecard.long_score, scorecard.short_score),
            timing_valid_until=timing,
        )
