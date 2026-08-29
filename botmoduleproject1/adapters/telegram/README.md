# Telegram adapter

Transport only. Sequence 10:

- `decoder.decode_update` turns a Telegram update dict into `TelegramInbound`
- `encoder.encode_receipt` turns a `CommandReceipt` into outbound text
- `RealTelegramTransport` **raises** — the Bot API is not bound

Commands are interpreted by `pm8_operator`, never here. This package must not
import strategy, risk, execution, or MT5 internals.
