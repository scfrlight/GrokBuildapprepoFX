from __future__ import annotations

import hashlib
from typing import Any

from botmoduleproject1.modules.pm7_persistence.integrity.canonicalization import canonical_dumps


def sha256_hex(payload: Any) -> str:
    data = canonical_dumps(payload).encode("utf-8")
    return hashlib.sha256(data).hexdigest()
