"""Lightweight in-process counters. No network, no broker."""

from __future__ import annotations


class Pm2Metrics:
    def __init__(self) -> None:
        self.scans: int = 0
        self.published_shortlist: int = 0
        self.suppressed: int = 0
        self.vetoes: int = 0

    def record_scan(self, *, shortlist: int, suppressed: int, vetoes: int) -> None:
        self.scans += 1
        self.published_shortlist += shortlist
        self.suppressed += suppressed
        self.vetoes += vetoes

    def snapshot(self) -> dict[str, int]:
        return {
            "scans": self.scans,
            "published_shortlist": self.published_shortlist,
            "suppressed": self.suppressed,
            "vetoes": self.vetoes,
        }
