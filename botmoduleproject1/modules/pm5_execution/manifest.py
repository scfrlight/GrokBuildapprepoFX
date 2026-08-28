from botmoduleproject1.modules.pm5_execution.capabilities import PM5_EXECUTION_METADATA


def module_manifest() -> dict:
    meta = PM5_EXECUTION_METADATA
    return {
        "name": meta.name,
        "version": meta.version,
        "role": "execution_truth_oms_ems",
        "depends_on": list(meta.dependencies),
        "accepts": ["RiskPublicationBundle"],
        "does_not": [
            "orders_to_mt5",
            "bypass_pm4",
            "increase_quantity",
            "flip_side",
            "allocate_risk",
            "durable_ledger",
        ],
        "modes": ["disabled", "shadow", "simulation"],
        "broker": "unavailable",
        "mt5": "placeholder_blocked",
        "durable": False,
        "execution_permitted_respected": True,
    }
