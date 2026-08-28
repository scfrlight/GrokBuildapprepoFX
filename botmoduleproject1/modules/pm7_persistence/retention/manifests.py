from botmoduleproject1.modules.pm7_persistence.integrity.hashing import sha256_hex


def archive_manifest(*, tier, sequence, frozen, checksum_tip) -> dict:
    payload = {"tier": getattr(tier, "value", tier), "sequence": sequence, "frozen": frozen, "tip": checksum_tip}
    payload["checksum"] = sha256_hex(payload)
    return payload
