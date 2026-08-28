# PM7 Persistence

Canonical append-only journal and evidence store for PM2–PM6 publications.

- Registered as `pm7_ledger` when `enable_pm7_persistence` is on.
- Default bind is `NullLedger`.
- `SIM-*` is simulation truth. Reconciliation without a venue stays degraded.
- Sequence 09 is not production durability. No MT5. No orders. No Telegram.
