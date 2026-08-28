"""Module registry: uniqueness, capabilities, dependency graph."""

from __future__ import annotations

from dataclasses import dataclass, field

from botmoduleproject1.app.capabilities import Capability, ModuleMetadata
from botmoduleproject1.app.exceptions import RegistryError
from botmoduleproject1.app.settings import ModulesSection


@dataclass
class RegisteredModule:
    metadata: ModuleMetadata
    instance: object


class ModuleRegistry:
    def __init__(self, policy: ModulesSection | None = None) -> None:
        self._policy = policy or ModulesSection()
        self._by_name: dict[str, RegisteredModule] = {}

    def register(self, metadata: ModuleMetadata, instance: object | None = None) -> None:
        name = metadata.name
        if name in self._by_name:
            raise RegistryError(f"duplicate module registration: {name}")
        if self._policy.allowlist and name not in self._policy.allowlist:
            raise RegistryError(f"module {name} is not on the allowlist")
        if name in self._policy.denylist:
            raise RegistryError(f"module {name} is denylisted")
        if not metadata.enabled:
            return
        self._by_name[name] = RegisteredModule(metadata=metadata, instance=instance or object())

    def get(self, name: str) -> RegisteredModule:
        try:
            return self._by_name[name]
        except KeyError as exc:
            raise RegistryError(f"unknown module: {name}") from exc

    def by_capability(self, capability: Capability) -> list[RegisteredModule]:
        return [m for m in self._by_name.values() if capability in m.metadata.capability_set]

    def names(self) -> tuple[str, ...]:
        return tuple(self._by_name.keys())

    def snapshot(self) -> dict[str, dict[str, object]]:
        return {
            name: {
                "version": item.metadata.version,
                "capabilities": [c.value for c in item.metadata.capabilities],
                "critical": item.metadata.critical,
                "api_version": item.metadata.api_version,
                "dependencies": list(item.metadata.dependencies),
            }
            for name, item in self._by_name.items()
        }

    def validate_dependencies(self) -> None:
        names = set(self._by_name)
        capabilities = {c.value for m in self._by_name.values() for c in m.metadata.capabilities}
        for item in self._by_name.values():
            for dep in item.metadata.dependencies:
                if dep in names or dep in capabilities:
                    continue
                raise RegistryError(
                    f"module {item.metadata.name} depends on missing {dep}"
                )
