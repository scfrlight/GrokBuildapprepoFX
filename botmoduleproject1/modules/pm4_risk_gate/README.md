# PM4 Risk Gate

Authoritative pre-trade capital-protection layer.

- Deny-by-default until PM2 + PM3-Strategy Engine + PM3 forecasting artifacts are valid.
- Converts analytical `TradeIntent` into a `RiskPublicationBundle` + `RiskVerdict`.
- **ALLOW is not an order.** PM5 remains closed. `execution_permitted` is always false.
- Kill-switch does not auto-rearm.
- In-memory control state is not a durable ledger (PM7/PM8).

Feature flag `enable_pm4_risk_gate` defaults false in YAML. Env opt-in, test/research only.

See `docs/architecture/pm4_risk_gate_integration_plan.md`.
