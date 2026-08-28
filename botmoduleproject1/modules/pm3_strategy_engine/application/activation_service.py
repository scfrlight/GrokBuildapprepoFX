from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from botmoduleproject1.contracts.v1.strategy_engine import (
    ProfileChangeAction,
    ProfileStatus,
    StrategyEventType,
    ValidationReport,
)
from botmoduleproject1.modules.pm3_strategy_engine.domain.entities import ProfileVersion
from botmoduleproject1.modules.pm3_strategy_engine.domain.events import StrategyLifecycleEvent
from botmoduleproject1.modules.pm3_strategy_engine.domain.policies import may_activate
from botmoduleproject1.modules.pm3_strategy_engine.infrastructure.seed import fingerprint
from botmoduleproject1.modules.pm3_strategy_engine.application.validation_service import ValidationService


class ActivationService:
    def __init__(self, profiles, versions, drafts, publisher) -> None:
        self.profiles = profiles
        self.versions = versions
        self.drafts = drafts
        self.publisher = publisher
        self.validation = ValidationService()

    def validate_draft(self, draft_id: str) -> ValidationReport:
        draft = self.drafts.get(draft_id)
        if draft is None:
            return ValidationReport(ok=False, errors=("unknown draft",))
        profile = self.profiles.get(draft.profile_id)
        if profile is None:
            return ValidationReport(ok=False, errors=("unknown profile",))
        return self.validation.validate_parameters(profile.schema, draft.parameters)

    def promote_version(self, draft_id: str, as_of: datetime) -> ProfileVersion:
        report = self.validate_draft(draft_id)
        if not report.ok:
            raise ValueError("; ".join(report.errors))
        draft = self.drafts.get(draft_id)
        assert draft is not None
        version = ProfileVersion(
            version_id=f"version:{draft.profile_id}:{uuid4().hex[:8]}",
            profile_id=draft.profile_id,
            status=ProfileStatus.TESTED,
            parameters=dict(draft.parameters),
            fingerprint=fingerprint(draft.parameters),
            created_at=as_of,
            parent_version_id=draft.source_version_id,
            immutable=False,
            notes="promoted from draft; not live trading",
        )
        self.versions.save(version)
        self.publisher.publish(
            StrategyLifecycleEvent(
                occurred_at=as_of,
                event_type=StrategyEventType.PROFILE_CHANGE,
                action=ProfileChangeAction.PROMOTE,
                profile_id=draft.profile_id,
                version_id=version.version_id,
                summary=f"promoted {version.version_id} to tested",
            )
        )
        return version

    def activate_version(self, version_id: str, as_of: datetime) -> ProfileVersion:
        version = self.versions.get(version_id)
        if version is None:
            raise ValueError("unknown version")
        if not may_activate(version.status):
            raise ValueError(f"status {version.status.value} cannot activate")
        profile = self.profiles.get(version.profile_id)
        if profile is None:
            raise ValueError("unknown profile")
        if profile.active_version_id:
            previous = self.versions.get(profile.active_version_id)
            if previous is not None and previous.version_id != version.version_id:
                previous.status = ProfileStatus.WATCHLIST
                previous.immutable = True
                self.versions.save(previous)
        version.status = ProfileStatus.ACTIVE
        version.immutable = True
        self.versions.save(version)
        profile.active_version_id = version.version_id
        profile.status = ProfileStatus.ACTIVE
        self.profiles.save(profile)
        self.publisher.publish(
            StrategyLifecycleEvent(
                occurred_at=as_of,
                event_type=StrategyEventType.PROFILE_CHANGE,
                action=ProfileChangeAction.ACTIVATE,
                profile_id=profile.profile_id,
                version_id=version.version_id,
                summary="activated in shadow/observe-only; not trading permission",
            )
        )
        return version
