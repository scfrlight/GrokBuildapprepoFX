"""Deterministic hashes for capital requests, policy, and decisions."""

from __future__ import annotations

import json
from hashlib import sha256
from typing import Any


def canonical_hash(payload: Any) -> str:
    blob = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return sha256(blob.encode("utf-8")).hexdigest()
