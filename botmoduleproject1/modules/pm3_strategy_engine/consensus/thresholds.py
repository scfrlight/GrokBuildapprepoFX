from botmoduleproject1.modules.pm3_strategy_engine.config.schema import ConsensusThresholds, ConsensusWeights

DEFAULT_WEIGHTS = ConsensusWeights()
DEFAULT_THRESHOLDS = ConsensusThresholds()


def vote_weight(h: float, r: float, q: float, f: float, live: float, weights: ConsensusWeights) -> float:
    return (
        weights.historical_reliability * h
        + weights.regime_fit * r
        + weights.setup_quality * q
        + weights.friction_fit * f
        + weights.recent_live_health * live
    )
