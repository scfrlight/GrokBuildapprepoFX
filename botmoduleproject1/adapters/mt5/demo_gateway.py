"""Sequence 11 Demo gateway. Not broker truth. Tickets are DEMO-*. Linux fail-closed for real terminal."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from botmoduleproject1.adapters.mt5.capabilities import BrokerCapabilities, probe_environment
from botmoduleproject1.app.exceptions import ExecutionDisabledError
from botmoduleproject1.contracts.v1.risk import RiskVerdictStatus


class DemoMt5Gateway:
    """Idempotent demo routing. Entry logic must not call this; use DemoRouter."""

    def __init__(
        self,
        *,
        capabilities: BrokerCapabilities | None = None,
        simulated: bool = True,
        max_retries: int = 2,
    ) -> None:
        self.capabilities = capabilities or probe_environment(force_terminal=simulated)
        self.simulated = simulated
        self.max_retries = max_retries
        self._by_client: dict[str, dict[str, Any]] = {}
        self._connected = False
        self.attempts: dict[str, int] = {}

    def connect(self) -> dict[str, Any]:
        if self.capabilities.account_kind != "demo":
            raise ExecutionDisabledError("non-demo MT5 account refused")
        if not self.simulated and not self.capabilities.terminal_present:
            raise ExecutionDisabledError("MT5 terminal absent; demo adapter fail-closed")
        self._connected = True
        return {"connected": True, "simulated": self.simulated, "account_kind": "demo"}

    def disconnect(self) -> None:
        self._connected = False

    def reconnect(self) -> dict[str, Any]:
        self.disconnect()
        return self.connect()

    def submit(
        self,
        *,
        client_order_id: str,
        symbol: str,
        side: str,
        quantity: str,
        verdict_status: str,
        intent_id: str | None = None,
    ) -> dict[str, Any]:
        if verdict_status != RiskVerdictStatus.ALLOW.value:
            raise ExecutionDisabledError("PM4 ALLOW required; entry must not talk to the venue")
        if not self._connected:
            return {
                "accepted": False,
                "state": "degraded",
                "reason": "disconnected",
                "venue_ticket": None,
                "silent_pass": False,
            }
        if client_order_id in self._by_client:
            existing = dict(self._by_client[client_order_id])
            existing["duplicate"] = True
            return existing
        n = self.attempts.get(client_order_id, 0) + 1
        self.attempts[client_order_id] = n
        if n > self.max_retries + 1:
            return {"accepted": False, "state": "rejected", "reason": "retry_exhausted", "duplicate": False}
        ticket = f"DEMO-{uuid4().hex[:12]}"
        row = {
            "accepted": True,
            "state": "filled" if self.simulated else "submitted",
            "venue_ticket": ticket,
            "venue_kind": "mt5_demo_sim" if self.simulated else "mt5_demo",
            "client_order_id": client_order_id,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "intent_id": intent_id,
            "duplicate": False,
            "broker_truth": False,
        }
        self._by_client[client_order_id] = row
        return dict(row)

    def reconcile(self, local_ref: str) -> dict[str, Any]:
        if not self._connected:
            return {"state": "degraded", "local_ref": local_ref, "venue_ref": None, "silent_pass": False}
        match = next((v for v in self._by_client.values() if v["client_order_id"] == local_ref or v["venue_ticket"] == local_ref), None)
        if match is None:
            return {"state": "unavailable", "local_ref": local_ref, "venue_ref": None, "silent_pass": False}
        return {"state": "matched_demo", "local_ref": local_ref, "venue_ref": match["venue_ticket"], "silent_pass": False}
