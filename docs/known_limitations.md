# Known limitations

- Not ready for demo trading, live trading, paper trading, or production.
- Fitted QRF is not implemented (**NOT-IN-SCOPE** / blocked).
- No real MT5 terminal on this host. Venue absence is UNAVAILABLE, not pass.
- Telegram Bot API unbound.
- Observability metrics are in-process; no remote scrape endpoint.
- Backup dump checksums differ across runs (UUIDs + timestamps). Compare `payload_canonical_sha256`.
- Master Orchestration Prompt file is **SOURCE-MISSING**; sequence *order* comes from the correction/authorization prompts.
- Original Drive `PM8a_Build_Spec.md` is **SOURCE-MISSING**; working copy is reconstructed.
- PM7 is a **PARTIAL evidence-journal subset**, not a production-durable warehouse and not the canonical downstream API.
- PM8 named projections (open orders, closed trades, performance, daily summary, operator dashboard) are **ABSENT**. Restore **apply** is **ABSENT**; restore **verification** exists.
- PM8 domain writes use JSON/TEXT, not Decimal money types.
- Sequence 15+ is **BLOCKED**.

Canonical copy of the Seq 14 limitations list: `docs/guides/known_limitations.md`.
