"""Sequence 15 Phase 1 — demo-only trading readiness allowlist (FSM gate).

Default is fail-closed. `trading_readiness` / `accept_trade` may become true
ONLY when every allowlist predicate holds (demo profile + env opt-in flag +
recovery/integrity/freshness). LIVE, paper, and production remain refused.

This path does NOT wire a real MT5 venue, Telegram Bot API, mobile BFF, or
live/production flags. PM4 remains the exclusive risk gate; readiness is not
an order send.
"""

from __future__ import annotations

from dataclasses import dataclass

from botmoduleproject1.app.profiles import ProfileName
from botmoduleproject1.app.settings import Settings

FLAG_FIELD = "demo_trading_readiness"

_REFUSED_TRADING_MODES = frozenset({"live", "paper"})
_REFUSED_CLI_MODES = frozenset({"live", "paper"})
_REFUSED_ENVIRONMENTS = frozenset({"production", "prod", "live"})


@dataclass(frozen=True)
class DemoReadinessDecision:
    """Outcome of the Sequence 15 demo-only readiness allowlist."""

    allowed: bool
    reasons: tuple[str, ...]
    path: str  # "closed" | "demo_allowlist"


def evaluate_demo_readiness_allowlist(
    settings: Settings,
    *,
    recovery_complete: bool,
    stale_data: bool,
    integrity_ok: bool,
) -> DemoReadinessDecision:
    """Return whether demo-only trading readiness may open.

    Fail closed unless the explicit DEMO allowlist path is satisfied.
    """
    live = (
        settings.profile is ProfileName.LIVE
        or settings.cli_mode == "live"
        or bool(settings.safety.live_trading_enabled)
        or settings.safety.trading_mode == "live"
    )
    if live:
        return DemoReadinessDecision(
            allowed=False,
            reasons=("live_fail_closed",),
            path="closed",
        )

    if (
        settings.safety.trading_mode in _REFUSED_TRADING_MODES
        or settings.cli_mode in _REFUSED_CLI_MODES
    ):
        return DemoReadinessDecision(
            allowed=False,
            reasons=("paper_or_live_mode_refused",),
            path="closed",
        )

    env = (settings.app.environment or "").strip().lower()
    if env in _REFUSED_ENVIRONMENTS:
        return DemoReadinessDecision(
            allowed=False,
            reasons=("production_environment_refused",),
            path="closed",
        )

    if settings.profile is not ProfileName.DEMO:
        return DemoReadinessDecision(
            allowed=False,
            reasons=("profile_not_demo", f"profile={settings.profile.value}"),
            path="closed",
        )

    flag_on = bool(getattr(settings.feature_flags, FLAG_FIELD, False))
    if not flag_on:
        return DemoReadinessDecision(
            allowed=False,
            reasons=("demo_trading_readiness_flag_off", "default_fail_closed"),
            path="closed",
        )

    opted = set(settings.feature_flags.env_opt_in)
    if FLAG_FIELD not in opted:
        return DemoReadinessDecision(
            allowed=False,
            reasons=("demo_trading_readiness_requires_env_opt_in",),
            path="closed",
        )

    if not recovery_complete:
        return DemoReadinessDecision(
            allowed=False,
            reasons=("recovery_incomplete",),
            path="closed",
        )
    if stale_data:
        return DemoReadinessDecision(
            allowed=False,
            reasons=("stale_data_safe_stop",),
            path="closed",
        )
    if not integrity_ok:
        return DemoReadinessDecision(
            allowed=False,
            reasons=("integrity_fail",),
            path="closed",
        )

    return DemoReadinessDecision(
        allowed=True,
        reasons=(
            "demo_allowlist_explicit",
            "pm4_remains_exclusive_risk_gate",
            "real_mt5_not_wired",
        ),
        path="demo_allowlist",
    )
