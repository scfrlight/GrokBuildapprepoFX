"""Sequence 11 — Demo-only broker capability checks. Live is refused."""

from __future__ import annotations

from dataclasses import dataclass
import sys


@dataclass(frozen=True)
class BrokerCapabilities:
    account_kind: str
    terminal_present: bool
    hedging: bool
    netting: bool
    expert_allowed: bool
    trade_allowed: bool
    symbol_filling: tuple[str, ...]
    live_disabled: bool = True

    @property
    def demo_ready(self) -> bool:
        return (
            self.account_kind == "demo"
            and self.terminal_present
            and self.trade_allowed
            and self.live_disabled
        )


def probe_environment(*, account_kind: str = "demo", force_terminal: bool | None = None) -> BrokerCapabilities:
    if account_kind != "demo":
        raise ValueError("live and non-demo account kinds are refused in Sequence 11")
    terminal = bool(force_terminal) if force_terminal is not None else sys.platform.startswith("win")
    return BrokerCapabilities(
        account_kind="demo",
        terminal_present=terminal,
        hedging=True,
        netting=False,
        expert_allowed=terminal,
        trade_allowed=terminal,
        symbol_filling=("FOK", "IOC"),
        live_disabled=True,
    )
