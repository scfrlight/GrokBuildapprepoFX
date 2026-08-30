# Known limitations

- Not ready for demo trading, live trading, paper trading, or production.
- Fitted QRF is not implemented.
- No real MT5 terminal on this host.
- Telegram Bot API unbound.
- Observability metrics are in-process; no remote scrape endpoint.
- Backup dump checksums differ across runs (UUIDs + timestamps). Compare `payload_canonical_sha256`.
- Master Orchestration Prompt file is still missing; sequence *order* comes from the correction/authorization prompts.
- Original PM8a Drive spec is SOURCE-MISSING (reconstructed copy in-repo).
- PM7 sqlite/file journals reload after restart but are not a production warehouse.
- PM8 named projections exist as read models; restore-apply is isolated SQLite or isolated PostgreSQL DSN (live target refused).
- PostgreSQL is implemented as a fail-closed PM8 backend. `production_durable` remains refused. Not a hosted production cluster claim.
- Sequence 15+ is blocked.

See also `docs/known_limitations.md` and `docs/ARCHITECTURE_INVENTORY.md`.

