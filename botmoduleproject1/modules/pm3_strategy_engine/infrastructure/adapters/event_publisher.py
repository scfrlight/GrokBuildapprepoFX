from __future__ import annotations

from botmoduleproject1.modules.pm3_strategy_engine.domain.events import StrategyLifecycleEvent


class InMemoryEventPublisher:
    def __init__(self) -> None:
        self.events: list[StrategyLifecycleEvent] = []

    def publish(self, event: StrategyLifecycleEvent) -> None:
        self.events.append(event)
