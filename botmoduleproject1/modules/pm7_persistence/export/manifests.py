def export_manifest(*, kind, event_ids, checksum, integrity) -> dict:
    return {
        "kind": kind,
        "event_ids": list(event_ids),
        "checksum": checksum,
        "integrity": integrity,
        "secrets": False,
    }
