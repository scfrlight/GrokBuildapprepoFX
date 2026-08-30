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
- PM8 named projections exist as rebuildable read models (not canonical truth). Isolated SQLite restore-apply exists; applying to the live store is refused. Isolated PostgreSQL restore-apply exists; live DSN is refused.
- Money keys on persist_* are Decimal/canonical strings. PostgreSQL stores `NUMERIC(28,8)`. Residual non-money JSON fields may still be untyped.
- SQLite outbox relay is local/test-only. PostgreSQL outbox uses `FOR UPDATE SKIP LOCKED`. `production_durable` remains refused — a running Postgres is not a production claim.
- Sequence 15+ is **BLOCKED**. Sequence 11+ trading enablement remains blocked.
- PM4 capital pipeline is exclusive to `pm4_risk_gate`. Historical “Seq 07 / PM5 risk gate” is not a second package. Approved executable intents still have `execution_allowed=false`. Drawdown restart-safety requires injected PM8 persistence.

Canonical copy of the Seq 14 limitations list: `docs/guides/known_limitations.md`.
