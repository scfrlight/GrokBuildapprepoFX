"""Process host. Heartbeat only — never sends orders."""

from __future__ import annotations

import time
from typing import Any

from botmoduleproject1.app.container import Container
from botmoduleproject1.app.diagnostics import DiagnosticsSnapshot, build_snapshot
from botmoduleproject1.app.exceptions import HealthError, PlatformError
from botmoduleproject1.app.health import CheckKind
from botmoduleproject1.app.lifecycle import LifecycleState
from botmoduleproject1.app.logging_config import get_logger


class Runtime:
    def __init__(self, container: Container) -> None:
        self.container = container
        self._stop = False
        self.last_snapshot: DiagnosticsSnapshot | None = None
        self._log = get_logger("botmoduleproject1.runtime")

    def start(self, *, heartbeat_ticks: int = 0) -> DiagnosticsSnapshot:
        """Run the boot sequence. heartbeat_ticks=0 means no loop (self-test)."""
        life = self.container.lifecycle
        settings = self.container.settings
        try:
            life.transition(LifecycleState.CONFIG_LOADED)
            life.transition(LifecycleState.VALIDATED)
            life.transition(LifecycleState.REGISTRY_READY)
            life.transition(LifecycleState.WIRED)
            startup = self.container.health.run(
                CheckKind.STARTUP, fail_on_critical=settings.health.fail_on_critical
            )
            life.transition(LifecycleState.STARTUP_CHECKED)
            life.transition(LifecycleState.WARMED)
            life.transition(LifecycleState.READY)
            ready = self.container.health.run(
                CheckKind.READINESS, fail_on_critical=False
            )
            if ready.passed:
                life.transition(LifecycleState.RUNNING)
            else:
                life.transition(LifecycleState.DEGRADED, reason=ready.summary)
            snapshot = self._snapshot(
                health={
                    "startup": startup.model_dump(mode="json"),
                    "readiness": ready.model_dump(mode="json"),
                }
            )
            for line in snapshot.banner_lines():
                self._log.info(line)
            ticks = heartbeat_ticks
            interval = settings.diagnostics.heartbeat_seconds
            while ticks > 0 and not self._stop:
                live = self.container.health.run(CheckKind.LIVENESS, fail_on_critical=False)
                self._log.info("heartbeat", liveness=live.passed, state=life.state.value)
                ticks -= 1
                if ticks > 0:
                    time.sleep(interval)
            return snapshot
        except PlatformError:
            life.fail("platform error")
            raise
        except Exception as exc:
            life.fail(str(exc))
            raise

    def stop(self) -> None:
        self._stop = True
        life = self.container.lifecycle
        if life.state in {LifecycleState.STOPPED, LifecycleState.FAILED}:
            return
        if life.state is not LifecycleState.STOPPING:
            try:
                life.transition(LifecycleState.STOPPING)
            except Exception:
                life.fail("stop")
                return
        try:
            life.transition(LifecycleState.STOPPED)
        except Exception:
            life.fail("stop")

    def _snapshot(self, health: dict[str, Any]) -> DiagnosticsSnapshot:
        self.last_snapshot = build_snapshot(
            self.container.settings,
            state=self.container.lifecycle.state,
            modules=self.container.registry.snapshot(),
            health=health,
        )
        return self.last_snapshot


def boot(
    container: Container, *, heartbeat_ticks: int = 0
) -> tuple[Runtime, DiagnosticsSnapshot]:
    runtime = Runtime(container)
    snapshot = runtime.start(heartbeat_ticks=heartbeat_ticks)
    return runtime, snapshot
