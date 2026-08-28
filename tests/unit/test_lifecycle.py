"""Lifecycle transitions are explicit and validated."""

from __future__ import annotations

import pytest

from botmoduleproject1.app.exceptions import LifecycleError
from botmoduleproject1.app.lifecycle import LifecycleManager, LifecycleState


def test_happy_path_to_running() -> None:
    life = LifecycleManager()
    assert life.state is LifecycleState.CREATED
    for state in (
        LifecycleState.CONFIG_LOADED,
        LifecycleState.VALIDATED,
        LifecycleState.REGISTRY_READY,
        LifecycleState.WIRED,
        LifecycleState.STARTUP_CHECKED,
        LifecycleState.WARMED,
        LifecycleState.READY,
        LifecycleState.RUNNING,
    ):
        life.transition(state)
    assert life.state is LifecycleState.RUNNING
    assert len(life.history) == 8


def test_illegal_transition() -> None:
    life = LifecycleManager()
    with pytest.raises(LifecycleError, match="illegal transition"):
        life.transition(LifecycleState.RUNNING)


def test_degraded_and_stop() -> None:
    life = LifecycleManager()
    for state in (
        LifecycleState.CONFIG_LOADED,
        LifecycleState.VALIDATED,
        LifecycleState.REGISTRY_READY,
        LifecycleState.WIRED,
        LifecycleState.STARTUP_CHECKED,
        LifecycleState.WARMED,
        LifecycleState.READY,
        LifecycleState.DEGRADED,
        LifecycleState.STOPPING,
        LifecycleState.STOPPED,
    ):
        life.transition(state)
    assert life.state is LifecycleState.STOPPED
