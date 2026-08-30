# PM7 Persistence

**PARTIAL / evidence-journal subset** (not a production-durable PM7 Master warehouse).

Canonical append-only journal and evidence store for PM2–PM6 publications.

- Registered as `pm7_ledger` when `enable_pm7_persistence` is on.
- Default bind is `NullLedger`.
- `SIM-*` is simulation truth. Reconciliation without a venue stays degraded.
- Sequence 09 (historical numbering) is not production durability. No MT5. No orders. No Telegram.
- Canonical downstream data API after correction is **PM8** `PersistenceApiV1`, not this package.
- File/sqlite backends reload committed journal rows, snapshots, and evidence on open.
- Backup in this module is metadata-only. Byte backup/restore verification and isolated restore-apply live in PM8 (`pm8_persistence`).


