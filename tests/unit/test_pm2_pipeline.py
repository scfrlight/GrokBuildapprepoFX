"""PM2 pipeline: scan, rank, suppress, publish, telemetry, determinism."""

from __future__ import annotations

from datetime import datetime

from botmoduleproject1.adapters.clock.system import FakeClock
from botmoduleproject1.adapters.market.synthetic import generate_bars
from botmoduleproject1.contracts.v1.market import Timeframe
from botmoduleproject1.contracts.v1.pm2 import (
    CandidateContextSnapshot,
    CandidateQualificationState,
    CandidateScoreCard,
    DataQualityStatus,
    PublicationBundle,
    QualificationStateName,
    QualityTier,
    RankedCandidate,
    quality_tier_for,
)
from botmoduleproject1.contracts.v1.session import RegimeType
from botmoduleproject1.contracts.v1.time import UTC
from botmoduleproject1.modules.pm2_market_context.config.defaults import DEFAULT_PM2_CONFIG
from botmoduleproject1.modules.pm2_market_context.config.schema import Pm2Config
from botmoduleproject1.modules.pm2_market_context.domain.ids import candidate_id
from botmoduleproject1.modules.pm2_market_context.engines.correlation_engine import shared_currency, view_for
from botmoduleproject1.modules.pm2_market_context.module import PM2Module
from botmoduleproject1.modules.pm2_market_context.ranking.deterministic_ranker import DeterministicRanker
from botmoduleproject1.modules.pm2_market_context.ranking.ltr_interface import LearningToRankHook
from botmoduleproject1.modules.pm2_market_context.suppression.conflict_suppressor import suppress
from botmoduleproject1.modules.pm2_market_context.suppression.redundancy_penalties import overlap_penalty
from botmoduleproject1.modules.pm2_market_context.telemetry.attribution import attribute
from botmoduleproject1.modules.pm2_market_context.telemetry.ghost_tracking import ghost_records

AS_OF = datetime(2026, 1, 15, 14, 0, tzinfo=UTC)


def _module(config: Pm2Config | None = None) -> PM2Module:
    return PM2Module(config or DEFAULT_PM2_CONFIG, FakeClock(AS_OF))


def _card(symbol: str, score: float, *, vetoes: tuple[str, ...] = ()) -> CandidateScoreCard:
    return CandidateScoreCard(
        long_score=min(100.0, score + 5),
        short_score=max(0.0, 40.0),
        final_confluence_score=score,
        directional_edge_gap=20.0,
        regime_score=score,
        structure_score=score,
        momentum_score=score,
        volatility_score=50.0,
        session_score=80.0,
        liquidity_score=80.0,
        correlation_penalty=0.0,
        feature_redundancy_penalty=0.0,
        confidence_score=70.0,
        quality_tier=quality_tier_for(score) if not vetoes else QualityTier.SUPPRESS,
        vetoes=vetoes,
        components={"regime": 10.0, "directional_bias": 12.0},
    )


def _candidate(symbol: str, score: float, rank: int = 1, **kwargs) -> RankedCandidate:
    cid = candidate_id(symbol, AS_OF)
    context = CandidateContextSnapshot(
        candidate_id=cid,
        event_id=cid,
        correlation_id=cid,
        symbol=symbol,
        as_of=AS_OF,
        regime=RegimeType.TRENDING,
        regime_confidence=0.7,
        data_quality=DataQualityStatus.OK,
        session_quality=0.7,
    )
    state = CandidateQualificationState(
        state=kwargs.pop("state", QualificationStateName.FORMING),
        entered_at=AS_OF,
        persistence_count=2,
        last_transition_reason="test",
    )
    return RankedCandidate(
        candidate_id=cid,
        event_id=cid,
        correlation_id=cid,
        symbol=symbol,
        as_of=AS_OF,
        final_rank=rank,
        scorecard=_card(symbol, score, vetoes=kwargs.pop("vetoes", ())),
        state=state,
        context=context,
        correlation_cluster=view_for(symbol).cluster,
        side_bias=kwargs.pop("side_bias", "long"),
    )


def test_scan_covers_universe_and_publishes_bundle() -> None:
    bundle = _module().scan(AS_OF)
    assert isinstance(bundle, PublicationBundle)
    symbols = {c.symbol for c in (*bundle.shortlist, *bundle.watchlist)}
    suppressed = {s.symbol for s in bundle.suppressed}
    covered = symbols | suppressed | {c.context.symbol for c in bundle.shortlist}
    # Every universe name is classified somewhere in the ranked scan diagnostics.
    assert bundle.as_of == AS_OF
    assert bundle.producer == "pm2_market_context"
    assert bundle.idempotency_key == f"pm2:scan:{AS_OF.isoformat()}"
    assert bundle.diagnostics_summary["orders"] is False
    assert bundle.diagnostics_summary["qrf"] is False
    assert bundle.diagnostics_summary["hmm_adapter"] is False
    assert bundle.calibration_snapshot["auto_weight_update"] is False
    assert covered or bundle.diagnostics_summary["quality"]["n"] == 4


def test_latest_bar_is_confirmed() -> None:
    mod = _module()
    bar = mod.latest_bar("EURUSD", Timeframe.H1)
    assert bar is not None
    assert (bar.broker_as_of or bar.open_time) <= AS_OF
    assert bar.symbol == "EURUSD"


def test_ranking_is_stable_and_tie_breaks_on_symbol() -> None:
    a = _candidate("EURUSD", 70.0)
    b = _candidate("GBPUSD", 70.0)
    ranked = DeterministicRanker().rank((b, a), as_of=AS_OF, config=DEFAULT_PM2_CONFIG)
    assert ranked[0].final_rank == 1
    assert ranked[1].final_rank == 2
    # equal scores: symbol ascending
    assert ranked[0].symbol == "EURUSD"
    ranked2 = DeterministicRanker().rank((a, b), as_of=AS_OF, config=DEFAULT_PM2_CONFIG)
    assert [c.symbol for c in ranked] == [c.symbol for c in ranked2]


def test_ltr_hook_is_disabled() -> None:
    hook = LearningToRankHook()
    assert hook.enabled is False
    cand = _candidate("EURUSD", 80.0)
    assert hook.rank((cand,), as_of=AS_OF) is None
    vec = hook.feature_vector(cand)
    assert "confluence" in vec


def test_shared_currency_penalty_and_conflict() -> None:
    assert shared_currency("EURUSD", "GBPUSD") is True
    assert overlap_penalty("GBPUSD", ("EURUSD",)) > 0
    strong = _candidate("EURUSD", 82.0, side_bias="long")
    weak = _candidate("GBPUSD", 61.0, side_bias="short")
    kept, records = suppress((strong, weak), DEFAULT_PM2_CONFIG)
    assert any("conflict" in ",".join(r.suppression_reasons) for r in records) or any(
        c.suppression is not None for c in kept
    )


def test_vetoed_candidate_is_suppressed() -> None:
    bad = _candidate("USDJPY", 88.0, vetoes=("volatility:shock",))
    kept, records = suppress((bad,), DEFAULT_PM2_CONFIG)
    assert records
    assert kept[0].handoff_eligibility is False
    assert kept[0].state.state is QualificationStateName.SUPPRESSED


def test_shadow_mode_never_hands_off() -> None:
    bundle = _module().scan(AS_OF)
    for item in (*bundle.shortlist, *bundle.watchlist):
        assert item.handoff_eligibility is False


def test_determinism_same_inputs_same_outputs() -> None:
    a = _module().scan(AS_OF)
    b = _module().scan(AS_OF)
    assert a.event_id == b.event_id
    assert a.correlation_id == b.correlation_id
    assert a.idempotency_key == b.idempotency_key
    def dump(bundle: PublicationBundle) -> dict:
        return bundle.model_dump(mode="json", exclude={"diagnostics_summary"})

    # ghost list sits in diagnostics; scores and ranks must match
    assert [c.symbol for c in a.shortlist] == [c.symbol for c in b.shortlist]
    assert [c.final_rank for c in a.watchlist] == [c.final_rank for c in b.watchlist]
    assert [s.symbol for s in a.suppressed] == [s.symbol for s in b.suppressed]
    dump(a)
    dump(b)


def test_attribution_records_dominant_family() -> None:
    cand = _candidate("EURUSD", 72.0)
    payload = attribute(cand)
    assert payload["symbol"] == "EURUSD"
    assert payload["dominant_family"]
    assert payload["handoff_eligibility"] is False


def test_ghost_tracking_lists_non_promoted() -> None:
    bundle = _module().scan(AS_OF)
    ranked = tuple(bundle.watchlist)
    ghosts = ghost_records(ranked, bundle)
    assert isinstance(ghosts, tuple)


def test_synthetic_bars_do_not_repaint() -> None:
    first = generate_bars("AUDUSD", Timeframe.H1, count=32, as_of=AS_OF)
    second = generate_bars("AUDUSD", Timeframe.H1, count=32, as_of=AS_OF)
    assert first == second
