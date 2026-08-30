# PM7 Persistence

**PARTIAL / evidence-journal subset** (not a production-durable PM7 Master warehouse).

Canonical append-only journal and evidence store for PM2–PM6 publications.

- Registered as `pm7_ledger` when `enable_pm7_persistence` is on.
- Default bind is `NullLedger`.
- `SIM-*` is simulation truth. Reconciliation without a venue stays degraded.
- Sequence 09 (historical numbering) is not production durability. No MT5. No orders. No Telegram.
- Canonical downstream data API after correction is **PM8** `PersistenceApiV1`, not this package.
- File/sqlite backends are write-append overlays; they do not reload history on restart.
- Backup in this module is metadata-only. Byte backup/restore verification is PM8a (`pm8_persistence`).

