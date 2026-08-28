"""Named configuration profiles. live is recognized and hard-blocked."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict

from botmoduleproject1.app.capabilities import Capability


class ProfileName(str, Enum):
    DEMO = "demo"
    TEST = "test"
    BACKTEST = "backtest"
    RESEARCH = "research"
    LIVE = "live"


class ProfilePolicy(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: ProfileName
    description: str
    allowed_capabilities: tuple[Capability, ...]
    forbidden_operations: tuple[str, ...]
    allows_mt5_demo_network: bool
    allows_live_network: bool
    allows_execution: bool
    may_enter_running: bool
    template: str


_PLATFORM = (
    Capability.PLATFORM,
    Capability.DIAGNOSTICS,
    Capability.TELEMETRY,
)

PROFILE_POLICIES: dict[ProfileName, ProfilePolicy] = {
    ProfileName.DEMO: ProfilePolicy(
        name=ProfileName.DEMO,
        description="MT5 Demo venue. Network to a demo account is allowed later; orders stay gated.",
        allowed_capabilities=_PLATFORM
        + (
            Capability.MARKET_DATA,
            Capability.RISK_GATING,
            Capability.STORAGE,
            Capability.NOTIFICATIONS,
        ),
        forbidden_operations=(
            "live_trading",
            "live_mt5",
            "production_ledger",
            "order_send",
        ),
        allows_mt5_demo_network=True,
        allows_live_network=False,
        allows_execution=False,
        may_enter_running=True,
        template="configs/demo.example.yaml",
    ),
    ProfileName.TEST: ProfilePolicy(
        name=ProfileName.TEST,
        description="Deterministic tests. No real external connections.",
        allowed_capabilities=_PLATFORM,
        forbidden_operations=(
            "live_trading",
            "live_network",
            "mt5_connect",
            "telegram",
            "order_send",
            "production_ledger",
        ),
        allows_mt5_demo_network=False,
        allows_live_network=False,
        allows_execution=False,
        may_enter_running=True,
        template="configs/test.example.yaml",
    ),
    ProfileName.BACKTEST: ProfilePolicy(
        name=ProfileName.BACKTEST,
        description="Historical replay. No live connections, no production ledger writes.",
        allowed_capabilities=_PLATFORM + (Capability.MARKET_DATA, Capability.STORAGE),
        forbidden_operations=(
            "live_trading",
            "live_network",
            "mt5_connect",
            "order_send",
            "production_ledger",
        ),
        allows_mt5_demo_network=False,
        allows_live_network=False,
        allows_execution=False,
        may_enter_running=True,
        template="configs/backtest.example.yaml",
    ),
    ProfileName.RESEARCH: ProfilePolicy(
        name=ProfileName.RESEARCH,
        description="Offline diagnostics and future PM9a studio. No order execution.",
        allowed_capabilities=_PLATFORM + (Capability.FORECASTING,),
        forbidden_operations=(
            "live_trading",
            "live_network",
            "mt5_connect",
            "order_send",
            "production_ledger",
        ),
        allows_mt5_demo_network=False,
        allows_live_network=False,
        allows_execution=False,
        may_enter_running=True,
        template="configs/research.example.yaml",
    ),
    ProfileName.LIVE: ProfilePolicy(
        name=ProfileName.LIVE,
        description="Recognized so a bad config is not coerced. Hard-blocked: cannot enter running.",
        allowed_capabilities=_PLATFORM,
        forbidden_operations=(
            "live_trading",
            "any_runtime",
            "order_send",
            "mt5_connect",
        ),
        allows_mt5_demo_network=False,
        allows_live_network=False,
        allows_execution=False,
        may_enter_running=False,
        template="configs/live.example.yaml",
    ),
}


def parse_profile(value: str | ProfileName) -> ProfileName:
    if isinstance(value, ProfileName):
        return value
    try:
        return ProfileName(str(value).strip().lower())
    except ValueError as exc:
        known = ", ".join(p.value for p in ProfileName)
        raise ValueError(f"unknown profile {value!r}; expected one of: {known}") from exc


def policy_for(name: str | ProfileName) -> ProfilePolicy:
    return PROFILE_POLICIES[parse_profile(name)]
