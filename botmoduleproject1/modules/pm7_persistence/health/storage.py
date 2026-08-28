def storage_ok(mode: str) -> bool:
    return mode != "production_durable"
