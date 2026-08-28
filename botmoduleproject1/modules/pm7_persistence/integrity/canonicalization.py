from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID


def canonical_dumps(payload: Any) -> str:
    return json.dumps(_normalize(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _normalize(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "model_dump"):
        return _normalize(value.model_dump(mode="python"))
    if isinstance(value, dict):
        return {str(k): _normalize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize(v) for v in value]
    return str(value)
