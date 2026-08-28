from botmoduleproject1.modules.pm3_strategy_engine.api.commands import COMMANDS
from botmoduleproject1.modules.pm3_strategy_engine.api.queries import QUERIES
from botmoduleproject1.modules.pm3_strategy_engine.capabilities import PM3_STRATEGY_ENGINE_METADATA


def module_manifest() -> dict:
    meta = PM3_STRATEGY_ENGINE_METADATA
    return {
        "name": meta.name,
        "display_name": "PM3-Strategy Engine",
        "version": meta.version,
        "capabilities": [c.value for c in meta.capabilities],
        "accepted_events": ["pm2.publication_bundle", "pm2.ranked_candidate", "synthetic.feedback"],
        "produced_events": ["strategy.vote", "strategy.consensus", "strategy.intent", "strategy.no_trade"],
        "queries": list(QUERIES),
        "commands": list(COMMANDS),
        "degradation": "NoTradeDecision / observe-only",
        "does_not": ["orders", "risk_allow", "mt5", "telegram", "qrf"],
    }
