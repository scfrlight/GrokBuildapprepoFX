# PM8 persistence (canonical Sequences 09–10)

Replaces the Sequence 00 `NullStorage` placeholder when `enable_pm8_persistence` is on.

- Sequence 09: consolidated families, 19 repository protocols, 20 services, versioned API v1, integrity/repair, backup/export, four idempotency edges, outbox/inbox.
- Sequence 10: migrations v1→v2 with rollback policy, backup schedules, restore verification, restart drills.

Default bind remains `NullStorage`. This module never sends orders, never talks to MT5, never treats `SIM-*` / `DEMO-*` as broker truth.
