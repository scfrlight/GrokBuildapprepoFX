"""MT5 adapter placeholder. Sequence 07: blocked. No MetaTrader5 import."""

from __future__ import annotations

from botmoduleproject1.app.exceptions import ExecutionDisabledError
from botmoduleproject1.contracts.v1.execution import NormalizedExecutionCommand


class Mt5BrokerAdapter:
    name = "mt5_placeholder"

    def available(self) -> bool:
        return False

    def submit(self, command: NormalizedExecutionCommand, *, now) -> list:
        raise ExecutionDisabledError("MT5 adapter is unavailable in Sequence 07")

    def cancel(self, command: NormalizedExecutionCommand, *, now) -> list:
        raise ExecutionDisabledError("MT5 adapter is unavailable in Sequence 07")

    def modify(self, command: NormalizedExecutionCommand, *, now) -> list:
        raise ExecutionDisabledError("MT5 adapter is unavailable in Sequence 07")

    def close(self, command: NormalizedExecutionCommand, *, now) -> list:
        raise ExecutionDisabledError("MT5 adapter is unavailable in Sequence 07")

    def fetch_open_orders(self) -> tuple:
        raise ExecutionDisabledError("MT5 adapter is unavailable in Sequence 07")

    def fetch_positions(self) -> tuple:
        raise ExecutionDisabledError("MT5 adapter is unavailable in Sequence 07")

    def health(self) -> dict:
        return {
            "adapter": self.name,
            "available": False,
            "status": "placeholder_blocked",
            "methods": {
                "submit": "blocked",
                "cancel": "blocked",
                "modify": "blocked",
                "close": "blocked",
                "fetch_open_orders": "blocked",
                "fetch_positions": "blocked",
            },
        }
