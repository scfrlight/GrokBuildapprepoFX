from __future__ import annotations

from datetime import datetime

from botmoduleproject1.contracts.v1.strategy_engine import ProfileChangeAction, StrategyEventType
from botmoduleproject1.modules.pm3_strategy_engine.domain.events import StrategyLifecycleEvent


class RollbackService:
    def __init__(self, bindings, versions, publisher) -> None:
        self.bindings = bindings
        self.versions = versions
        self.publisher = publisher

    def rollback_binding(self, binding_id: str, as_of: datetime):
        binding = self.bindings.get(binding_id)
        if binding is None:
            raise ValueError("unknown binding")
        if not binding.previous_version_id:
            raise ValueError("no previous version to roll back to")
        previous = self.versions.get(binding.previous_version_id)
        if previous is None:
            raise ValueError("previous version missing")
        current = binding.version_id
        binding.previous_version_id = current
        binding.version_id = previous.version_id
        self.bindings.save(binding)
        self.publisher.publish(
            StrategyLifecycleEvent(
                occurred_at=as_of,
                event_type=StrategyEventType.PROFILE_CHANGE,
                action=ProfileChangeAction.ROLLBACK,
                profile_id=binding.profile_id,
                version_id=previous.version_id,
                symbol=binding.symbol,
                summary=f"rolled back binding {binding_id}",
                attributes={"from": current, "to": previous.version_id},
            )
        )
        return binding
