from botmoduleproject1.modules.pm4_risk_gate.capabilities import PM4_RISK_GATE_METADATA


def module_manifest() -> dict:
    meta = PM4_RISK_GATE_METADATA
    return {
        "name": meta.name,
        "display_name": "PM4 Risk Gate",
        "version": meta.version,
        "capabilities": [c.value for c in meta.capabilities],
        "accepted_events": [
            "pm2.ranked_candidate",
            "pm3.trade_intent",
            "pm3.forecast_output",
        ],
        "produced_events": [
            "risk.verdict",
            "risk.publication_bundle",
            "risk.kill_switch",
            "risk.incident",
        ],
        "degradation": "deny-by-default / freeze / kill_protected",
        "does_not": ["orders", "mt5", "telegram", "alpha", "side_flip", "auto_rearm"],
        "durable": False,
    }
