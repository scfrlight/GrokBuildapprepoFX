from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from botmoduleproject1.contracts.v1.strategy_engine import ProfileChangeAction, ProfileStatus
from botmoduleproject1.modules.pm3_strategy_engine.domain.entities import StrategyDraft
from botmoduleproject1.modules.pm3_strategy_engine.domain.events import StrategyLifecycleEvent
from botmoduleproject1.modules.pm3_strategy_engine.domain.policies import may_edit
from botmoduleproject1.contracts.v1.strategy_engine import StrategyEventType


class DraftService:
    def __init__(self, versions, drafts, profiles, publisher) -> None:
        self.versions = versions
        self.drafts = drafts
        self.profiles = profiles
        self.publisher = publisher

    def clone_draft(self, profile_id: str, as_of: datetime) -> StrategyDraft:
        profile = self.profiles.get(profile_id)
        if profile is None or profile.active_version_id is None:
            raise ValueError("profile or active version missing")
        source = self.versions.get(profile.active_version_id)
        if source is None:
            raise ValueError("active version missing")
        draft = StrategyDraft(
            draft_id=f"draft:{profile_id}:{uuid4().hex[:8]}",
            profile_id=profile_id,
            source_version_id=source.version_id,
            parameters=dict(source.parameters),
            created_at=as_of,
            updated_at=as_of,
        )
        self.drafts.save(draft)
        self.publisher.publish(
            StrategyLifecycleEvent(
                occurred_at=as_of,
                event_type=StrategyEventType.PROFILE_CHANGE,
                action=ProfileChangeAction.CLONE_DRAFT,
                profile_id=profile_id,
                version_id=source.version_id,
                summary=f"cloned draft {draft.draft_id}",
            )
        )
        return draft

    def update_draft_parameter(self, draft_id: str, name: str, value, as_of: datetime) -> StrategyDraft:
        draft = self.drafts.get(draft_id)
        if draft is None:
            raise ValueError("unknown draft")
        params = dict(draft.parameters)
        params[name] = value
        draft.parameters = params
        draft.updated_at = as_of
        self.drafts.save(draft)
        self.publisher.publish(
            StrategyLifecycleEvent(
                occurred_at=as_of,
                event_type=StrategyEventType.PROFILE_CHANGE,
                action=ProfileChangeAction.UPDATE_DRAFT,
                profile_id=draft.profile_id,
                summary=f"updated {name} on {draft_id}",
                attributes={"name": name},
            )
        )
        return draft

    def apply_preset(self, draft_id: str, preset_name: str, as_of: datetime) -> StrategyDraft:
        draft = self.drafts.get(draft_id)
        if draft is None:
            raise ValueError("unknown draft")
        profile = self.profiles.get(draft.profile_id)
        if profile is None:
            raise ValueError("unknown profile")
        match = next((p for p in profile.presets if p.name == preset_name), None)
        if match is None:
            raise ValueError("unknown preset")
        draft.parameters = dict(match.parameters)
        draft.updated_at = as_of
        self.drafts.save(draft)
        self.publisher.publish(
            StrategyLifecycleEvent(
                occurred_at=as_of,
                event_type=StrategyEventType.PROFILE_CHANGE,
                action=ProfileChangeAction.APPLY_PRESET,
                profile_id=draft.profile_id,
                summary=f"applied preset {preset_name}",
            )
        )
        return draft

    def assert_active_immutable(self, version_id: str) -> None:
        version = self.versions.get(version_id)
        if version is None:
            raise ValueError("unknown version")
        if not may_edit(version.status, version.immutable):
            raise ValueError("active/immutable version cannot be edited in place")
