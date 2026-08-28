"""Registry uniqueness, capabilities, dependency graph."""

from __future__ import annotations

import pytest

from botmoduleproject1.app.capabilities import Capability, ModuleMetadata
from botmoduleproject1.app.exceptions import RegistryError
from botmoduleproject1.app.registry import ModuleRegistry
from botmoduleproject1.app.settings import ModulesSection


def _meta(name: str, deps: tuple[str, ...] = (), caps: tuple[Capability, ...] = (Capability.DIAGNOSTICS,)) -> ModuleMetadata:
    return ModuleMetadata(name=name, version="0.0.0", capabilities=caps, dependencies=deps)


def test_duplicate_registration_rejected() -> None:
    registry = ModuleRegistry()
    registry.register(_meta("alpha"))
    with pytest.raises(RegistryError, match="duplicate"):
        registry.register(_meta("alpha"))


def test_missing_dependency_rejected() -> None:
    registry = ModuleRegistry()
    registry.register(_meta("child", deps=("parent",)))
    with pytest.raises(RegistryError, match="missing parent"):
        registry.validate_dependencies()


def test_capability_lookup() -> None:
    registry = ModuleRegistry()
    registry.register(_meta("risk", caps=(Capability.RISK_GATING,)))
    found = registry.by_capability(Capability.RISK_GATING)
    assert len(found) == 1
    assert found[0].metadata.name == "risk"


def test_denylist() -> None:
    registry = ModuleRegistry(ModulesSection(denylist=("blocked",)))
    with pytest.raises(RegistryError, match="denylist"):
        registry.register(_meta("blocked"))


def test_allowlist() -> None:
    registry = ModuleRegistry(ModulesSection(allowlist=("keep",)))
    registry.register(_meta("keep"))
    with pytest.raises(RegistryError, match="allowlist"):
        registry.register(_meta("other"))
