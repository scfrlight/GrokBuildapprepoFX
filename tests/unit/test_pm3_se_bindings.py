from __future__ import annotations

import pytest

from botmoduleproject1.contracts.v1.strategy_engine import ProfileStatus, StrategyTemplateType
from tests.unit.pm3se_support import AS_OF, engine


def test_three_active_branches_per_symbol() -> None:
    mod = engine()
    active = [b for b in mod.bindings.list_for_symbol("EURUSD") if b.active]
    assert len(active) == 3
    types = {b.template_type for b in active}
    assert StrategyTemplateType.TREND_PULLBACK in types
    assert StrategyTemplateType.MEAN_REVERSION in types


def test_duplicate_and_max_three_rejected() -> None:
    mod = engine()
    profile = next(p for p in mod.profiles.list_all() if p.template_type is StrategyTemplateType.TREND_PULLBACK)
    with pytest.raises(ValueError, match="duplicate|max"):
        mod.binding_service.replace_active("EURUSD", profile.profile_id, AS_OF)


def test_disabled_profile_cannot_bind() -> None:
    mod = engine()
    profile = mod.profiles.list_all()[0]
    profile.status = ProfileStatus.DISABLED
    mod.profiles.save(profile)
    with pytest.raises(ValueError, match="disabled"):
        mod.binding_service.replace_active("GBPUSD", profile.profile_id, AS_OF)


def test_replace_after_deactivate() -> None:
    mod = engine()
    profile = next(p for p in mod.profiles.list_all() if p.template_type is StrategyTemplateType.TREND_PULLBACK)
    replaced = mod.binding_service.replace_active(
        "EURUSD",
        profile.profile_id,
        AS_OF,
        deactivate_template=StrategyTemplateType.TREND_PULLBACK.value,
    )
    assert replaced.active is True
    active = [b for b in mod.bindings.list_for_symbol("EURUSD") if b.active]
    assert len(active) == 3
