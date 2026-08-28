from __future__ import annotations

from botmoduleproject1.modules.pm3_strategy_engine.domain.entities import SymbolStrategyBinding


class InMemoryBindingRepository:
    def __init__(self) -> None:
        self._items: dict[str, SymbolStrategyBinding] = {}

    def get(self, binding_id: str) -> SymbolStrategyBinding | None:
        return self._items.get(binding_id)

    def save(self, binding: SymbolStrategyBinding) -> None:
        self._items[binding.binding_id] = binding

    def list_for_symbol(self, symbol: str) -> tuple[SymbolStrategyBinding, ...]:
        return tuple(b for b in self._items.values() if b.symbol == symbol)

    def list_all(self) -> tuple[SymbolStrategyBinding, ...]:
        return tuple(self._items.values())
