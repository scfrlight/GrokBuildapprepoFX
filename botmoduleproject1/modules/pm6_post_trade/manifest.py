from botmoduleproject1.modules.pm6_post_trade.capabilities import PM6_POST_TRADE_METADATA


def module_manifest() -> dict:
    meta = PM6_POST_TRADE_METADATA
    return {
        "name": meta.name,
        "version": meta.version,
        "role": "post_trade_surveillance_governance",
        "depends_on": list(meta.dependencies),
        "accepts": ["ExecutionPublicationBundle", "RiskPublicationBundle"],
        "does_not": [
            "orders",
            "mt5",
            "bypass_pm4",
            "bypass_pm5",
            "fabricate_broker_truth",
            "durable_ledger",
            "telegram",
        ],
        "truth": "simulation_or_degraded",
        "durable": False,
        "lanes": ["operator", "control"],
    }
