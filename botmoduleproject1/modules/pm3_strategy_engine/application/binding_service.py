from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from botmoduleproject1.contracts.v1.strategy_engine import (
    ProfileChangeAction,
    ProfileStatus,
    StrategyEventType,
)
from botmoduleproject1.modules.pm3_strategy_engine.domain.entities import SymbolStrategyBinding
from botmoduleproject1.modules.pm3_strategy_engine.domain.events import StrategyLifecycleEvent
from botmoduleproject1.modules.pm3_strategy_engine.application.validation_service import ValidationService


class SymbolBindingService:
    def __init__(self, bindings, profiles, versions, publisher, max_active: int = 3) -> None:
        self.bindings = bindings
        self.profiles = profiles
        self.versions = versions
        self.publisher = publisher
        self.max_active = max_active
        self.validation = ValidationService()

    def list_for_symbol(self, symbol: str) -> tuple[SymbolStrategyBinding, ...]:
        return self.bindings.list_for_symbol(symbol)

    def list_all(self) -> tuple[SymbolStrategyBinding, ...]:
        return self.bindings.list_all()

    def replace_active(
        self,
        symbol: str,
        profile_id: str,
        as_of: datetime,
        *,
        deactivate_template: str | None = None,
    ) -> SymbolStrategyBinding:
        profile = self.profiles.get(profile_id)
        if profile is None or profile.active_version_id is None:
            raise ValueError("profile missing active version")
        if profile.status in {ProfileStatus.DISABLED, ProfileStatus.DEGRADED, ProfileStatus.RETIRED}:
            raise ValueError("disabled profile cannot bind as active")
        version = self.versions.get(profile.active_version_id)
        if version is None:
            raise ValueError("version missing")
        current = list(self.bindings.list_for_symbol(symbol))
        previous_version = None
        if deactivate_template:
            for item in current:
                if item.template_type.value == deactivate_template and item.active:
                    previous_version = item.version_id
                    item.active = False
                    self.bindings.save(item)
        binding = SymbolStrategyBinding(
            binding_id=f"bind:{symbol}:{profile.template_type.value}:{uuid4().hex[:6]}",
            symbol=symbol,
            profile_id=profile_id,
            version_id=version.version_id,
            template_type=profile.template_type,
            active=True,
            created_at=as_of,
            previous_version_id=previous_version,
        )
        self.bindings.save(binding)
        report = self.validation.validate_bindings(
            self.bindings.list_for_symbol(symbol), max_active=self.max_active
        )
        if not report.ok:
            binding.active = False
            self.bindings.save(binding)
            raise ValueError("; ".join(report.errors))
        self.publisher.publish(
            StrategyLifecycleEvent(
                occurred_at=as_of,
                event_type=StrategyEventType.PROFILE_CHANGE,
                action=ProfileChangeAction.REPLACE_BINDING,
                profile_id=profile_id,
                version_id=version.version_id,
                symbol=symbol,
                summary=f"replaced binding on {symbol}",
            )
        )
        return binding
