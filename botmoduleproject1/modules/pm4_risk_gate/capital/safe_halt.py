"""Safe-halt latch. Manual recovery only. No auto-rearm."""

from __future__ import annotations


class SafeHaltController:
    def __init__(self) -> None:
        self.halted = False
        self.reason = ""

    def trip(self, reason: str) -> None:
        self.halted = True
        self.reason = reason

    def recover(self, *, actor: str, reason: str) -> None:
        if not actor or actor == "automatic":
            raise ValueError("safe-halt recovery must be explicit and non-automatic")
        self.halted = False
        self.reason = f"recovered:{reason}"
