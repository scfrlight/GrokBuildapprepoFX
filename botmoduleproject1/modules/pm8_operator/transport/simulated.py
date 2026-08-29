"""In-process operator transport. No network. Not Telegram."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.operator import CommandReceipt, OperatorCommand, TelegramOutbound


class SimulatedTransport:
    mode = "simulated"

    def __init__(self) -> None:
        self.inbox: list[OperatorCommand] = []
        self.outbox: list[TelegramOutbound] = []

    def deliver_in(self, command: OperatorCommand) -> None:
        self.inbox.append(command)

    def deliver_out(self, receipt: CommandReceipt, chat_id: str = "console") -> TelegramOutbound:
        message = TelegramOutbound(chat_id=chat_id, text=_format_receipt(receipt))
        self.outbox.append(message)
        return message


def _format_receipt(receipt: CommandReceipt) -> str:
    return (
        f"[{receipt.disposition.value}] {receipt.verb.value}\n"
        f"{receipt.message}\n"
        f"reason={receipt.reason_code} actor={receipt.actor_id}\n"
        f"order=false pm4_skip=false mt5=false"
    )
