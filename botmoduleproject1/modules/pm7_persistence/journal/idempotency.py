from botmoduleproject1.modules.pm7_persistence.integrity.hashing import sha256_hex


def payload_fingerprint(event) -> str:
    return sha256_hex(event.event_payload)
