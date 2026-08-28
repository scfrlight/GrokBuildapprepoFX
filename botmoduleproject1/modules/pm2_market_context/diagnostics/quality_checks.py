"""Snapshot quality diagnostics."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.pm2 import DataQualityStatus
from botmoduleproject1.modules.pm2_market_context.scanner.universe_scanner import SymbolSnapshot


def quality_summary(snapshots: tuple[SymbolSnapshot, ...]) -> dict[str, object]:
    counts: dict[str, int] = {}
    for snap in snapshots:
        counts[snap.quality.value] = counts.get(snap.quality.value, 0) + 1
    ok = all(s.quality is DataQualityStatus.OK for s in snapshots)
    return {
        "ok": ok,
        "n": len(snapshots),
        "counts": counts,
        "eligible": sum(1 for s in snapshots if s.eligible),
    }
