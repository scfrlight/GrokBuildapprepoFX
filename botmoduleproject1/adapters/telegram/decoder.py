"""Decode Telegram update dicts. No business logic. No network."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from botmoduleproject1.contracts.v1.operator import TelegramInbound
from botmoduleproject1.contracts.v1.time import ensure_aware_utc


def decode_update(payload: dict[str, Any]) -> TelegramInbound:
    message = payload.get("message") or payload.get("edited_message") or {}
    chat = message.get("chat") or {}
    user = message.get("from") or {}
    date_raw = message.get("date")
    if isinstance(date_raw, (int, float)):
        occurred = datetime.fromtimestamp(date_raw, tz=timezone.utc)
    elif isinstance(date_raw, datetime):
        occurred = ensure_aware_utc(date_raw, "date")
    else:
        occurred = datetime.now(tz=timezone.utc)
    return TelegramInbound(
        update_id=int(payload.get("update_id") or 0),
        user_id=str(user.get("id") or ""),
        username=user.get("username"),
        chat_id=str(chat.get("id") or ""),
        text=str(message.get("text") or ""),
        occurred_at=occurred,
    )
