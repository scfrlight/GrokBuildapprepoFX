from botmoduleproject1.modules.pm7_persistence.config.defaults import GENESIS_HASH
from botmoduleproject1.modules.pm7_persistence.integrity.hashing import sha256_hex


def next_hash(previous: str, canonical_payload) -> str:
    return sha256_hex({"previous": previous or GENESIS_HASH, "payload": canonical_payload})
