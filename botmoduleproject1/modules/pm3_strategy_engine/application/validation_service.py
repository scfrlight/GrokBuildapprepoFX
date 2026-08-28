from __future__ import annotations

from typing import Any

from botmoduleproject1.contracts.v1.strategy_engine import ValidationReport
from botmoduleproject1.contracts.v1.tuning import ParameterSchema
from botmoduleproject1.modules.pm3_strategy_engine.domain.entities import SymbolStrategyBinding
from botmoduleproject1.modules.pm3_strategy_engine.infrastructure.seed import fingerprint


class ValidationService:
    def validate_parameters(
        self, schema: tuple[ParameterSchema, ...], params: dict[str, Any]
    ) -> ValidationReport:
        errors: list[str] = []
        for item in schema:
            if item.name not in params:
                errors.append(f"missing parameter {item.name}")
                continue
            value = params[item.name]
            if item.type == "float":
                try:
                    number = float(value)
                except (TypeError, ValueError):
                    errors.append(f"{item.name} must be float")
                    continue
                if item.min is not None and number < item.min:
                    errors.append(f"{item.name} below min")
                if item.max is not None and number > item.max:
                    errors.append(f"{item.name} above max")
            elif item.type == "int":
                if not isinstance(value, int) or isinstance(value, bool):
                    errors.append(f"{item.name} must be int")
                    continue
                if item.min is not None and value < item.min:
                    errors.append(f"{item.name} below min")
                if item.max is not None and value > item.max:
                    errors.append(f"{item.name} above max")
            if item.allowed_values and value not in item.allowed_values:
                errors.append(f"{item.name} not in allowed_values")
        return ValidationReport(
            ok=not errors,
            errors=tuple(errors),
            fingerprint=fingerprint(params) if not errors else None,
        )

    def validate_bindings(
        self,
        bindings: tuple[SymbolStrategyBinding, ...],
        *,
        max_active: int = 3,
    ) -> ValidationReport:
        errors: list[str] = []
        by_symbol: dict[str, list[SymbolStrategyBinding]] = {}
        for item in bindings:
            if not item.active:
                continue
            by_symbol.setdefault(item.symbol, []).append(item)
        for symbol, group in by_symbol.items():
            if len(group) > max_active:
                errors.append(f"{symbol} has {len(group)} active branches (max {max_active})")
            types = [b.template_type for b in group]
            if len(types) != len(set(types)):
                errors.append(f"{symbol} has duplicate template bindings")
            profiles = [b.profile_id for b in group]
            if len(profiles) != len(set(profiles)):
                errors.append(f"{symbol} has duplicate profile bindings")
        return ValidationReport(ok=not errors, errors=tuple(errors))
