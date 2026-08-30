"""Sequence 11 — the only path from an ALLOW verdict to the demo gateway.

Strategy / entry code must not import DemoMt5Gateway.
"""

from __future__ import annotations

from typing import Any

from botmoduleproject1.adapters.mt5.demo_gateway import DemoMt5Gateway
from botmoduleproject1.app.exceptions import ExecutionDisabledError
from botmoduleproject1.contracts.v1.risk import RiskVerdict, RiskVerdictStatus


class DemoRouter:
    def __init__(self, gateway: DemoMt5Gateway, persistence_api: Any | None = None) -> None:
        self.gateway = gateway
        self.api = persistence_api

    def route(self, verdict: RiskVerdict, *, client_order_id: str, quantity: str) -> dict[str, Any]:
        if verdict.status is not RiskVerdictStatus.ALLOW:
            raise ExecutionDisabledError("router refuses non-ALLOW verdicts")
        result = self.gateway.submit(
            client_order_id=client_order_id,
            symbol=getattr(verdict, "symbol", None) or "EURUSD",
            side="buy",
            quantity=quantity,
            verdict_status=verdict.status.value,
            intent_id=str(verdict.intent_id),
        )
        if self.api is not None and result.get("accepted"):
            self.api.persist_order(client_order_id, {"state": result["state"], "ticket": result.get("venue_ticket")})
            self.api.persist_execution(
                order_id=client_order_id,
                venue_kind=result.get("venue_kind", "mt5_demo_sim"),
                payload=result,
                venue_ticket=result.get("venue_ticket"),
                venue_callback_id=result.get("venue_ticket"),
            )
        elif self.api is not None and not result.get("accepted"):
            self.api.persist_reconciliation(
                local_ref=client_order_id,
                venue_ref=None,
                state="degraded",
                detail={"reason": result.get("reason")},
            )
        return result
