"""Encode receipts as Telegram outbound text. No business logic."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.operator import CommandReceipt, TelegramOutbound


def encode_receipt(receipt: CommandReceipt, *, chat_id: str) -> TelegramOutbound:
    text = (
        f"{receipt.verb.value}: {receipt.disposition.value}\n"
        f"{receipt.message}\n"
        f"{receipt.reason_code}"
    )
    return TelegramOutbound(chat_id=chat_id, text=text)
