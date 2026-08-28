"""Headless control surface for a future PM9. No Telegram imports."""

from __future__ import annotations

from datetime import datetime
from typing import Any


class StrategyControlBridgeService:
    def __init__(self, *, profiles, bindings, drafts, activation, rollback, trackers, health) -> None:
        self.profiles = profiles
        self.bindings = bindings
        self.drafts = drafts
        self.activation = activation
        self.rollback = rollback
        self.trackers = trackers
        self.health = health

    def list_symbols(self) -> tuple[str, ...]:
        return tuple(sorted({b.symbol for b in self.bindings.list_all()}))

    def list_available_strategies(self) -> list[dict[str, Any]]:
        return [
            {
                "profile_id": p.profile_id,
                "name": p.name,
                "template": p.template_type.value,
                "status": p.status.value,
                "active_version_id": p.active_version_id,
            }
            for p in self.profiles.list_all()
        ]

    def list_active_strategies_by_symbol(self, symbol: str) -> list[dict[str, Any]]:
        return [
            {
                "binding_id": b.binding_id,
                "profile_id": b.profile_id,
                "version_id": b.version_id,
                "template": b.template_type.value,
            }
            for b in self.bindings.list_for_symbol(symbol)
            if b.active
        ]

    def get_tuning_schema(self, profile_id: str) -> list[dict[str, Any]]:
        profile = self.profiles.get(profile_id)
        if profile is None:
            return []
        return [s.model_dump(mode="json") for s in profile.schema]

    def get_bindings(self) -> list[dict[str, Any]]:
        return [
            {
                "binding_id": b.binding_id,
                "symbol": b.symbol,
                "profile_id": b.profile_id,
                "version_id": b.version_id,
                "active": b.active,
                "template": b.template_type.value,
            }
            for b in self.bindings.list_all()
        ]

    def compact_summary(self, symbol: str) -> dict[str, Any]:
        return {
            "symbol": symbol,
            "active": self.list_active_strategies_by_symbol(symbol),
            "observe_only": True,
            "telegram": False,
        }
