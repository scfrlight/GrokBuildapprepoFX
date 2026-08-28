from __future__ import annotations

from botmoduleproject1.modules.pm3_strategy_engine.domain.entities import (
    ProfileVersion,
    StrategyDraft,
    StrategyProfile,
)


class InMemoryProfileRepository:
    def __init__(self) -> None:
        self._items: dict[str, StrategyProfile] = {}

    def get(self, profile_id: str) -> StrategyProfile | None:
        return self._items.get(profile_id)

    def save(self, profile: StrategyProfile) -> None:
        self._items[profile.profile_id] = profile

    def list_all(self) -> tuple[StrategyProfile, ...]:
        return tuple(self._items.values())


class InMemoryVersionRepository:
    def __init__(self) -> None:
        self._items: dict[str, ProfileVersion] = {}

    def get(self, version_id: str) -> ProfileVersion | None:
        return self._items.get(version_id)

    def save(self, version: ProfileVersion) -> None:
        self._items[version.version_id] = version

    def list_for_profile(self, profile_id: str) -> tuple[ProfileVersion, ...]:
        return tuple(v for v in self._items.values() if v.profile_id == profile_id)


class InMemoryDraftRepository:
    def __init__(self) -> None:
        self._items: dict[str, StrategyDraft] = {}

    def get(self, draft_id: str) -> StrategyDraft | None:
        return self._items.get(draft_id)

    def save(self, draft: StrategyDraft) -> None:
        self._items[draft.draft_id] = draft
