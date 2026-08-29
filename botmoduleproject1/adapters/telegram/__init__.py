"""Telegram adapter. Encode/decode only. No trading logic. No Bot API in Sequence 10."""

from botmoduleproject1.adapters.telegram.decoder import decode_update
from botmoduleproject1.adapters.telegram.encoder import encode_receipt
from botmoduleproject1.adapters.telegram.transport import RealTelegramTransport

__all__ = ["decode_update", "encode_receipt", "RealTelegramTransport"]
