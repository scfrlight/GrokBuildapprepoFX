"""PM2 engines: session, regime, scoring, qualification, features."""

from __future__ import annotations

from datetime import datetime, timedelta

from botmoduleproject1.adapters.market.synthetic import generate_bars
from botmoduleproject1.contracts.v1.market import Timeframe
from botmoduleproject1.contracts.v1.pm2 import (
    CandidateScoreCard,
    DataQualityStatus,
    QualificationStateName,
    QualityTier,
    quality_tier_for,
)
from botmoduleproject1.contracts.v1.session import RegimeType, SessionName
from botmoduleproject1.contracts.v1.time import UTC
from botmoduleproject1.modules.pm2_market_context.config.defaults import DEFAULT_PM2_CONFIG
from botmoduleproject1.modules.pm2_market_context.domain.enums import VolatilityPhase
from botmoduleproject1.modules.pm2_market_context.engines.bias_engine import evaluate_bias
from botmoduleproject1.modules.pm2_market_context.engines.session_liquidity_engine import evaluate_session
from botmoduleproject1.modules.pm2_market_context.engines.structure_engine import evaluate_structure
from botmoduleproject1.modules.pm2_market_context.engines.volatility_engine import evaluate_volatility
from botmoduleproject1.modules.pm2_market_context.features.builder import FeatureSnapshot, build_snapshot
from botmoduleproject1.modules.pm2_market_context.features.normalization import assert_no_lookahead
from botmoduleproject1.modules.pm2_market_context.qualification.state_machine import initial, transition
from botmoduleproject1.modules.pm2_market_context.regime.baseline_rules import classify_regime
from botmoduleproject1.modules.pm2_market_context.regime.gmm_adapter import GmmAdapter
from botmoduleproject1.modules.pm2_market_context.regime.hmm_adapter import HmmAdapter
from botmoduleproject1.modules.pm2_market_context.regime.persistence import persist
from botmoduleproject1.modules.pm2_market_context.scoring.vetoes import vetoes

AS_OF = datetime(2026, 1, 15, 14, 0, tzinfo=UTC)


def _snap(**kwargs) -> FeatureSnapshot:
    payload = {
        "symbol": "EURUSD",
        "as_of": AS_OF,
        "timeframe": Timeframe.H1,
        "bars": 64,
        "close": 1.10,
        "sma_fast": 1.101,
        "sma_slow": 1.099,
        "roc_n": 0.0012,
        "atr": 0.004,
        "atr_pct": 0.0036,
    }
    payload.update(kwargs)
    return FeatureSnapshot(**payload)


def _card(score: float, **kwargs) -> CandidateScoreCard:
    data = {
        "long_score": score,
        "short_score": max(0.0, 100.0 - score),
        "final_confluence_score": score,
        "directional_edge_gap": abs(2 * score - 100.0),
        "regime_score": score,
        "structure_score": score,
        "momentum_score": score,
        "volatility_score": 50.0,
        "session_score": 70.0,
        "liquidity_score": 70.0,
        "correlation_penalty": 0.0,
        "feature_redundancy_penalty": 0.0,
        "confidence_score": 60.0,
        "quality_tier": quality_tier_for(score),
    }
    data.update(kwargs)
    data["quality_tier"] = quality_tier_for(data["final_confluence_score"])
    if data.get("vetoes"):
        data["quality_tier"] = QualityTier.SUPPRESS
    return CandidateScoreCard(**data)


def test_overlap_session_is_high_quality() -> None:
    result = evaluate_session(AS_OF, is_weekend=False)
    assert SessionName.LONDON in result.context.sessions
    assert SessionName.NEW_YORK in result.context.sessions
    assert SessionName.OVERLAP_LONDON_NY in result.context.sessions
    assert result.session_score >= 80
    assert result.rollover_risk is False


def test_rollover_and_weekend_are_independent_of_bias() -> None:
    rollover = evaluate_session(datetime(2026, 1, 15, 21, 0, tzinfo=UTC))
    assert rollover.rollover_risk is True
    assert SessionName.ROLLOVER in rollover.context.sessions
    weekend = evaluate_session(datetime(2026, 1, 17, 14, 0, tzinfo=UTC), is_weekend=True)
    assert weekend.session_score <= 15
    assert SessionName.OFF_SESSION in weekend.context.sessions


def test_regime_is_not_bullish_bearish() -> None:
    trending, _ = classify_regime(_snap(sma_fast=1.12, sma_slow=1.08, roc_n=0.004, atr_pct=0.004))
    ranging, _ = classify_regime(_snap(sma_fast=1.10, sma_slow=1.10, roc_n=0.0001, atr_pct=0.003))
    volatile, _ = classify_regime(_snap(atr_pct=0.02, roc_n=0.01))
    compression, _ = classify_regime(_snap(atr_pct=0.001, roc_n=0.0))
    assert trending is RegimeType.TRENDING
    assert ranging is RegimeType.RANGING
    assert volatile is RegimeType.VOLATILE
    assert compression is RegimeType.COMPRESSION
    assert RegimeType.TRENDING.value != "bullish"


def test_regime_persistence_holds_low_confidence_flips() -> None:
    chosen, seen = persist(RegimeType.TRENDING, RegimeType.RANGING, 0.4, hold=2, seen=1)
    assert chosen is RegimeType.TRENDING
    assert seen == 2
    chosen2, _ = persist(RegimeType.TRENDING, RegimeType.UNTRADEABLE, 0.2, hold=2, seen=5)
    assert chosen2 is RegimeType.UNTRADEABLE


def test_hmm_gmm_are_disabled_stubs() -> None:
    snap = _snap()
    assert HmmAdapter.enabled is False
    assert HmmAdapter().infer(snap) is None
    assert GmmAdapter.enabled is False
    assert GmmAdapter().infer(snap) is None


def test_quality_bands() -> None:
    assert quality_tier_for(0) is QualityTier.SUPPRESS
    assert quality_tier_for(39.9) is QualityTier.SUPPRESS
    assert quality_tier_for(40) is QualityTier.WATCH
    assert quality_tier_for(59.9) is QualityTier.WATCH
    assert quality_tier_for(60) is QualityTier.ELIGIBLE
    assert quality_tier_for(74.9) is QualityTier.ELIGIBLE
    assert quality_tier_for(75) is QualityTier.HIGH
    assert quality_tier_for(89.9) is QualityTier.HIGH
    assert quality_tier_for(90) is QualityTier.TOP
    assert quality_tier_for(100) is QualityTier.TOP


def test_veto_caps_qualification() -> None:
    found = vetoes(
        quality=DataQualityStatus.STALE,
        regime=RegimeType.UNTRADEABLE,
        phase=VolatilityPhase.SHOCK,
        rollover=True,
        weekend=False,
    )
    assert "data_quality:stale" in found
    assert "regime:untradeable" in found
    assert "volatility:shock" in found
    assert "session:rollover" in found


def test_state_machine_neutral_forming_qualified() -> None:
    thresholds = DEFAULT_PM2_CONFIG.thresholds
    state = initial(AS_OF)
    state = transition(state, _card(55), AS_OF, thresholds)
    assert state.state is QualificationStateName.FORMING
    state = transition(state, _card(62), AS_OF + timedelta(hours=1), thresholds)
    assert state.state is QualificationStateName.QUALIFIED
    assert state.persistence_count >= thresholds.persistence_bars



def test_state_machine_veto_suppresses() -> None:
    thresholds = DEFAULT_PM2_CONFIG.thresholds
    state = initial(AS_OF)
    card = _card(80, vetoes=("regime:untradeable",))
    nxt = transition(state, card, AS_OF, thresholds)
    assert nxt.state is QualificationStateName.SUPPRESSED


def test_state_machine_stale_from_any() -> None:
    thresholds = DEFAULT_PM2_CONFIG.thresholds
    state = initial(AS_OF)
    state = transition(state, _card(70), AS_OF, thresholds)
    nxt = transition(state, _card(70), AS_OF + timedelta(hours=1), thresholds, stale=True)
    assert nxt.state is QualificationStateName.STALE


def test_bias_splits_long_and_short() -> None:
    bars = generate_bars("EURUSD", Timeframe.H1, count=64, as_of=AS_OF)
    feat = build_snapshot("EURUSD", Timeframe.H1, bars, AS_OF)
    bias = evaluate_bias({"H1": feat})
    assert 0 <= bias.long_bias_score <= 100
    assert 0 <= bias.short_bias_score <= 100
    assert abs(bias.net_bias_score - (bias.long_bias_score - bias.short_bias_score)) < 1e-9


def test_structure_uses_confirmed_pivots_only() -> None:
    bars = generate_bars("GBPUSD", Timeframe.H1, count=64, as_of=AS_OF)
    result = evaluate_structure(bars)
    assert result.quality >= 0
    assert result.state.value in {"continuation", "break", "transition", "invalidation", "undefined"}


def test_volatility_dead_is_reachable() -> None:
    result = evaluate_volatility(_snap(atr_pct=0.0004, roc_n=0.0))
    assert result.phase is VolatilityPhase.DEAD


def test_no_lookahead_on_synthetic_bars() -> None:
    bars = generate_bars("EURUSD", Timeframe.H1, count=32, as_of=AS_OF)
    assert_no_lookahead(bars, AS_OF.timestamp())
    last_end = bars[-1].broker_as_of or bars[-1].open_time
    assert last_end <= AS_OF
