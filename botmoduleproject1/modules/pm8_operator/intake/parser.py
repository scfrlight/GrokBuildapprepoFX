"""Slash-text → verb. No trading semantics."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.operator import OperatorVerb

_ALIASES: dict[str, OperatorVerb] = {
    "help": OperatorVerb.HELP,
    "start": OperatorVerb.HELP,
    "status": OperatorVerb.STATUS,
    "health": OperatorVerb.HEALTH,
    "doctor": OperatorVerb.DOCTOR,
    "pending": OperatorVerb.PENDING,
    "alerts": OperatorVerb.LIST_ALERTS,
    "list_alerts": OperatorVerb.LIST_ALERTS,
    "journal": OperatorVerb.QUERY_JOURNAL,
    "query": OperatorVerb.QUERY_JOURNAL,
    "ack": OperatorVerb.ACK,
    "acknowledge": OperatorVerb.ACK,
    "halt": OperatorVerb.HALT,
    "stop": OperatorVerb.HALT,
    "kill": OperatorVerb.HALT,
    "approve": OperatorVerb.APPROVE,
    "reject": OperatorVerb.REJECT,
    "deny": OperatorVerb.REJECT,
    "propose": OperatorVerb.PROPOSE_TUNING,
    "tune": OperatorVerb.PROPOSE_TUNING,
    "buy": OperatorVerb.BUY,
    "sell": OperatorVerb.SELL,
    "order": OperatorVerb.PLACE_ORDER,
    "place": OperatorVerb.PLACE_ORDER,
    "trade": OperatorVerb.PLACE_ORDER,
    "resume": OperatorVerb.RESUME,
    "rearm": OperatorVerb.REARM,
    "live": OperatorVerb.ENABLE_LIVE,
    "enable_live": OperatorVerb.ENABLE_LIVE,
    "mt5": OperatorVerb.CONNECT_MT5,
    "connect": OperatorVerb.CONNECT_MT5,
}


def parse_text(text: str) -> tuple[OperatorVerb, str | None, dict[str, str]]:
    raw = (text or "").strip()
    if raw.startswith("/"):
        raw = raw[1:]
    if not raw:
        return OperatorVerb.HELP, None, {}
    parts = raw.split()
    head = parts[0].lower().replace("-", "_")
    verb = _ALIASES.get(head, OperatorVerb.HELP if head in {"?", "h"} else None)
    if verb is None:
        # Unknown tokens that look like orders are refused, not help.
        if head in {"long", "short", "market", "limit", "close"}:
            return OperatorVerb.PLACE_ORDER, None, {"raw": text}
        return OperatorVerb.HELP, None, {"unknown": head}
    target = parts[1] if len(parts) > 1 else None
    payload: dict[str, str] = {}
    if verb is OperatorVerb.PROPOSE_TUNING and len(parts) >= 3:
        payload = {"parameter": parts[1], "new_value": " ".join(parts[2:])}
        target = parts[1]
    elif target:
        payload = {"target_id": target}
    return verb, target, payload
