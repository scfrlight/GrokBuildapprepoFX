"""In-process hooks only. Not Sequence 15 observability."""

from __future__ import annotations

from collections import Counter
from time import perf_counter
from typing import Any


class CapitalMetrics:
    def __init__(self) -> None:
        self.evaluations = 0
        self.by_state: Counter[str] = Counter()
        self.failed_checks: Counter[str] = Counter()
        self.last_latency_ms: float = 0.0

    def start(self) -> float:
        return perf_counter()

    def observe(self, *, state: str, failed: tuple[str, ...], started: float) -> dict[str, Any]:
        self.evaluations += 1
        self.by_state[state] += 1
        for name in failed:
            self.failed_checks[name] += 1
        self.last_latency_ms = (perf_counter() - started) * 1000.0
        return {
            "evaluations": self.evaluations,
            "state": state,
            "latency_ms": round(self.last_latency_ms, 3),
            "failed": list(failed),
        }
