"""Explicit lifecycle state machine. Invalid transitions raise.

Sequence 02 inserts PREFLIGHT_CHECKED between VALIDATED and REGISTRY_READY.
That is the documented initialize → validate → preflight → connect/wire path.
"""

from __future__ import annotations

from enum import Enum

from botmoduleproject1.app.exceptions import LifecycleError
from botmoduleproject1.contracts.v1.time import utc_now


class LifecycleState(str, Enum):
    CREATED = "created"
    CONFIG_LOADED = "config_loaded"
    VALIDATED = "validated"
    PREFLIGHT_CHECKED = "preflight_checked"
    REGISTRY_READY = "registry_ready"
    WIRED = "wired"
    STARTUP_CHECKED = "startup_checked"
    WARMED = "warmed"
    READY = "ready"
    RUNNING = "running"
    DEGRADED = "degraded"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


_ALLOWED: dict[LifecycleState, frozenset[LifecycleState]] = {
    LifecycleState.CREATED: frozenset(
        {LifecycleState.CONFIG_LOADED, LifecycleState.FAILED}
    ),
    LifecycleState.CONFIG_LOADED: frozenset(
        {LifecycleState.VALIDATED, LifecycleState.FAILED}
    ),
    LifecycleState.VALIDATED: frozenset(
        {LifecycleState.PREFLIGHT_CHECKED, LifecycleState.FAILED}
    ),
    LifecycleState.PREFLIGHT_CHECKED: frozenset(
        {LifecycleState.REGISTRY_READY, LifecycleState.FAILED}
    ),
    LifecycleState.REGISTRY_READY: frozenset(
        {LifecycleState.WIRED, LifecycleState.FAILED}
    ),
    LifecycleState.WIRED: frozenset(
        {LifecycleState.STARTUP_CHECKED, LifecycleState.FAILED}
    ),
    LifecycleState.STARTUP_CHECKED: frozenset(
        {LifecycleState.WARMED, LifecycleState.FAILED}
    ),
    LifecycleState.WARMED: frozenset({LifecycleState.READY, LifecycleState.FAILED}),
    LifecycleState.READY: frozenset(
        {
            LifecycleState.RUNNING,
            LifecycleState.DEGRADED,
            LifecycleState.STOPPING,
            LifecycleState.FAILED,
        }
    ),
    LifecycleState.RUNNING: frozenset(
        {LifecycleState.DEGRADED, LifecycleState.STOPPING, LifecycleState.FAILED}
    ),
    LifecycleState.DEGRADED: frozenset(
        {LifecycleState.RUNNING, LifecycleState.STOPPING, LifecycleState.FAILED}
    ),
    LifecycleState.STOPPING: frozenset(
        {LifecycleState.STOPPED, LifecycleState.FAILED}
    ),
    LifecycleState.STOPPED: frozenset(),
    LifecycleState.FAILED: frozenset(),
}


class LifecycleManager:
    def __init__(self) -> None:
        self.state = LifecycleState.CREATED
        self.history: list[tuple[str, LifecycleState, LifecycleState]] = []

    def can_transition(self, target: LifecycleState) -> bool:
        return target in _ALLOWED[self.state]

    def transition(self, target: LifecycleState, *, reason: str = "") -> LifecycleState:
        if target is self.state:
            return self.state
        if target not in _ALLOWED[self.state]:
            raise LifecycleError(
                f"illegal transition {self.state.value} -> {target.value}"
            )
        previous = self.state
        self.state = target
        stamp = utc_now().isoformat()
        self.history.append((stamp, previous, target))
        return self.state

    def fail(self, reason: str = "unspecified") -> LifecycleState:
        if self.state is not LifecycleState.FAILED:
            if LifecycleState.FAILED in _ALLOWED[self.state]:
                self.transition(LifecycleState.FAILED, reason=reason)
            else:
                previous = self.state
                self.state = LifecycleState.FAILED
                self.history.append((utc_now().isoformat(), previous, self.state))
        return self.state
