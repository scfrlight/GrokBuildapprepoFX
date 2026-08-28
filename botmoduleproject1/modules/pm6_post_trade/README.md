# PM6 — Post-Trade Controls

Continuous post-trade monitoring, two-lines-of-defence surveillance, incidents,
and governance intelligence.

- Consumes PM5 `ExecutionPublicationBundle` and PM4 `RiskPublicationBundle`.
- `SIM-*` is simulation truth, never an MT5 ticket.
- Reconciliation without a venue stays `degraded`.
- Never creates orders. Never calls a broker. Never sizes risk.
- In-memory only (`non_durable_before_pm7`).
- Bound only when `enable_pm6_post_trade` is on; otherwise `NullMonitoring`.
