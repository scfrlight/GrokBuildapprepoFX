# Known limitations

- Not ready for demo trading, live trading, or production.
- Fitted QRF is not implemented.
- No real MT5 terminal on this host.
- Telegram Bot API unbound.
- Observability metrics are in-process; no remote scrape endpoint.
- Backup dump checksums differ across runs (UUIDs + timestamps). Compare `payload_canonical_sha256`.
- Master Orchestration Prompt file is still missing; sequence *order* comes from the correction/authorization prompts.
- Sequence 15+ is blocked.
