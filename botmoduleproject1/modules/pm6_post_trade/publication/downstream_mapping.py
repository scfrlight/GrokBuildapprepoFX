def for_pm7(bundle) -> dict:
    return {
        "bundle_id": str(bundle.bundle_id),
        "durable": False,
        "handoff": "non_durable_before_pm7",
        "producer": bundle.producer,
    }
