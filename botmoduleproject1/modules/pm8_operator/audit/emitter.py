"""In-memory command audit. Never logs secrets. Not a durable ledger."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.operator import CommandReceipt, OperatorCommand

_SECRET_MARKERS = ("token", "password", "secret", "api_key", "authorization")


def _clean(text: str) -> str:
    lowered = text.lower()
    if any(marker in lowered for marker in _SECRET_MARKERS):
        return "[redacted]"
    return text


class CommandAudit:
    def __init__(self) -> None:
        self.records: list[dict] = []

    def record(self, command: OperatorCommand, receipt: CommandReceipt) -> dict:
        row = {
            "idempotency_key": receipt.idempotency_key,
            "verb": command.verb.value,
            "actor_id": command.actor.actor_id,
            "role": command.actor.role.value,
            "disposition": receipt.disposition.value,
            "reason_code": receipt.reason_code,
            "text": _clean(command.text),
            "occurred_at": receipt.occurred_at.isoformat(),
            "creates_order": False,
            "skips_pm4": False,
        }
        self.records.append(row)
        return row

    def snapshot(self, *, limit: int = 50) -> tuple[dict, ...]:
        return tuple(self.records[-limit:])
