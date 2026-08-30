# PM4 Risk Gate

Authoritative pre-trade capital-protection layer.

- Deny-by-default until PM2 + PM3-Strategy Engine + PM3 forecasting artifacts are valid.
- Converts analytical `TradeIntent` into a `RiskPublicationBundle` + `RiskVerdict`.
- **ALLOW is not an order.** PM5 remains closed. `execution_permitted` is always false.
- Capital pipeline: `evaluate_capital(RiskEvaluationRequest)` — forty checks, Decimal
  sizing, PM8 persist, replay, fail-closed. An approved executable intent still has
  `execution_allowed=false`. Historical “Seq 07 / PM5 risk” title maps here (canonical Seq 06).
- Kill-switch / safe-halt do not auto-rearm.
- In-memory control state is not a durable ledger unless PersistenceApiV1 is injected.

Feature flag `enable_pm4_risk_gate` defaults false in YAML. Env opt-in, test/research only.

See `docs/guides/pm4_capital_gate.md` and `docs/architecture/pm4_risk_gate_integration_plan.md`.
