# Known limitations

- Not ready for demo trading, live trading, paper trading, or production.
- Fitted QRF is not implemented (**NOT-IN-SCOPE** / blocked).
- No real MT5 terminal on this host. Venue absence is UNAVAILABLE, not pass.
- Telegram Bot API unbound.
- Observability metrics are in-process; no remote scrape endpoint.
- Backup dump checksums differ across runs (UUIDs + timestamps). Compare `payload_canonical_sha256`.
- Master Orchestration Prompt file is **SOURCE-MISSING**; sequence *order* comes from the correction/authorization prompts.
- Original Drive `PM8a_Build_Spec.md` is **SOURCE-MISSING**; working copy is reconstructed (`RECONSTRUCTED-SOURCE`).
- `PM7_Master_Prompt.md` is **SOURCE-MISSING**. PM7 sqlite/file journals now reload; the module is still not a production-durable warehouse and not the canonical downstream API.
- PM8 named projections exist as rebuildable read models (not canonical truth). Isolated SQLite restore-apply exists; applying to the live store is refused. PostgreSQL restore-apply is **BLOCKED**.
- Money keys on persist_* are Decimal/canonical strings. Residual non-money JSON fields may still be untyped.
- SQLite outbox relay is local/test-only. PostgreSQL production durability is **BLOCKED**.
- Sequence 15+ is **BLOCKED**.

Canonical copy of the Seq 14 limitations list: `docs/guides/known_limitations.md`.
