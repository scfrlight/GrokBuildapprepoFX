"""PM3-Strategy Engine profile / draft / version governance."""

from __future__ import annotations

import pytest

from botmoduleproject1.contracts.v1.strategy_engine import ProfileStatus
from tests.unit.pm3se_support import AS_OF, engine


def test_clone_active_to_draft_and_immutability() -> None:
    mod = engine()
    profile = next(p for p in mod.profiles.list_all() if p.status is ProfileStatus.ACTIVE)
    draft = mod.draft_service.clone_draft(profile.profile_id, AS_OF)
    assert draft.source_version_id == profile.active_version_id
    with pytest.raises(ValueError, match="immutable"):
        mod.draft_service.assert_active_immutable(profile.active_version_id)


def test_parameter_validation_range() -> None:
    mod = engine()
    profile = mod.profiles.list_all()[0]
    ok = mod.activation.validation.validate_parameters(
        profile.schema, {"historical_reliability": 0.6, "recent_live_health": 0.4, "lookback": 20}
    )
    assert ok.ok is True
    bad = mod.activation.validation.validate_parameters(
        profile.schema, {"historical_reliability": 2.0, "recent_live_health": 0.4, "lookback": 20}
    )
    assert bad.ok is False


def test_promote_activate_rollback_events() -> None:
    mod = engine()
    profile = mod.profiles.list_all()[0]
    original = profile.active_version_id
    draft = mod.draft_service.clone_draft(profile.profile_id, AS_OF)
    mod.draft_service.update_draft_parameter(draft.draft_id, "lookback", 25, AS_OF)
    report = mod.activation.validate_draft(draft.draft_id)
    assert report.ok is True
    promoted = mod.activation.promote_version(draft.draft_id, AS_OF)
    assert promoted.status is ProfileStatus.TESTED
    assert promoted.parent_version_id == original
    activated = mod.activation.activate_version(promoted.version_id, AS_OF)
    assert activated.status is ProfileStatus.ACTIVE
    assert activated.immutable is True
    previous = mod.versions.get(original)
    assert previous is not None
    assert previous.status is ProfileStatus.WATCHLIST
    kinds = [e.action.value for e in mod.publisher.events if e.action is not None]
    assert "clone_draft" in kinds
    assert "promote" in kinds
    assert "activate" in kinds


def test_deterministic_rollback_binding() -> None:
    mod = engine()
    profile = next(p for p in mod.profiles.list_all() if p.status is ProfileStatus.ACTIVE)
    original = profile.active_version_id
    draft = mod.draft_service.clone_draft(profile.profile_id, AS_OF)
    mod.draft_service.update_draft_parameter(draft.draft_id, "lookback", 30, AS_OF)
    promoted = mod.activation.promote_version(draft.draft_id, AS_OF)
    mod.activation.activate_version(promoted.version_id, AS_OF)
    replaced = mod.binding_service.replace_active(
        "EURUSD",
        profile.profile_id,
        AS_OF,
        deactivate_template=profile.template_type.value,
    )
    assert replaced.previous_version_id == original or replaced.previous_version_id == promoted.version_id
    rolled = mod.rollback.rollback_binding(replaced.binding_id, AS_OF)
    assert rolled.version_id == replaced.previous_version_id or rolled.version_id == original
    assert any(e.action and e.action.value == "rollback" for e in mod.publisher.events)


def test_no_implicit_activation_from_draft() -> None:
    mod = engine()
    profile = mod.profiles.list_all()[0]
    active_before = profile.active_version_id
    draft = mod.draft_service.clone_draft(profile.profile_id, AS_OF)
    refreshed = mod.profiles.get(profile.profile_id)
    assert refreshed is not None
    assert refreshed.active_version_id == active_before
    assert draft.draft_id != active_before
