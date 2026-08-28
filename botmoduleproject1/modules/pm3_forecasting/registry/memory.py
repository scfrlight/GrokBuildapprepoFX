"""In-memory model registry. Not PM8. Not durable."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.forecasting import ModelVersionInfo
from botmoduleproject1.modules.pm3_forecasting.domain.ids import memory_registry_uri, registry_key


class InMemoryModelRegistry:
    def __init__(self) -> None:
        self._items: dict[str, ModelVersionInfo] = {}

    def register(self, info: ModelVersionInfo) -> ModelVersionInfo:
        stored = info
        if stored.registry_uri is None:
            stored = stored.model_copy(
                update={"registry_uri": memory_registry_uri(info.model_id, info.version)}
            )
        self._items[registry_key(stored.model_id, stored.version)] = stored
        return stored

    def get(self, model_id: str, version: str) -> ModelVersionInfo | None:
        return self._items.get(registry_key(model_id, version))

    def latest(self, model_id: str) -> ModelVersionInfo | None:
        matches = [v for k, v in self._items.items() if k.startswith(f"{model_id}:")]
        if not matches:
            return None
        return matches[-1]
