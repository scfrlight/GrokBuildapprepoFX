# BOTMODULEPROJECT1 — SEQUENCE 06
# PM4 Risk Gate: Adaptive Risk Allocation, Uncertainty-Aware Position Sizing, Portfolio Heat, Concentration Governance, Drawdown Governor, Pre-Trade Controls & Kill-Switch

Persisted verbatim from the Sequence 06 source-of-truth prompt (2026-08-28).
Original `PM4_Master_Prompt.md` was not recovered from Drive/GitHub.

This file is the Sequence 06 specification. Implementation lives in
`botmoduleproject1/modules/pm4_risk_gate/`. Integration plan:
`docs/architecture/pm4_risk_gate_integration_plan.md`.

---

PM4 is the authoritative pre-trade capital protection layer. It sits after
PM2 candidate quality / ranking / context, after PM3-Strategy Engine
TradeIntent, after PM3 forecasting / QRF ForecastOutput, and before PM5
execution.

PM4 is NOT a signal engine, market scanner, predictive inference engine,
strategy engine, broker execution module, Telegram/UI layer, or a
monolithic all-in-one bot.

Non-negotiable safety rules:

1. Capital preservation first.
2. Deny-by-default until all required artifacts are valid.
3. No TradeIntent may pass to execution without explicit PM4 ALLOW.
4. PM4 must not generate alpha.
5. PM4 must not modify signal direction to "improve" strategy outcomes.
6. PM4 may reduce, cap, freeze, deny, throttle, or kill.
7. PM4 must not execute orders directly.
8. PM4 must not own broker connection logic.
9. PM4 must not be bypassable by PM3-Strategy Engine, PM3 forecasting, CLI,
   config, feature flag, or operator command.
10. Stale, malformed, inconsistent, missing, schema-incompatible, or
    ambiguous PM2/PM3 artifacts must cause DENY or safer degraded behavior.
11. Recovery after freeze/kill must be explicit, controlled, policy-driven,
    and auditable.
12. No hidden auto-rearm after kill-switch.
13. Risk-reducing actions may later be allowed under restrictive modes;
    risk-increasing actions remain blocked when protection requires it.
14. No fake "healthy" state on insufficient evidence.
15. No order-capable object should be created by PM4; only risk-governed
    handoff artifacts for future PM5.

Pipeline:

PM2 Candidate Context + PM3-Strategy Engine TradeIntent + PM3 forecasting /
QRF ForecastOutput → Risk Intake Validation → Risk Admission Check →
Hierarchical Risk Budgeting → Concentration / Correlation Assessment →
Effective Portfolio Heat → Uncertainty-Aware Position Sizing → Drawdown
Governor → Pre-Trade Controls → Kill-Switch → Risk Publication Bundle →
Downstream Handoff Eligibility for future PM5.

Feature flag: `enable_pm4_risk_gate` (requires-review, YAML default false,
env opt-in, test/research only). Even if enabled, PM5 remains closed.

Forbidden in Sequence 06: broker connection, real MT5, order send, real
cancel/replace, durable ledger, database migrations, Telegram, PM5
execution logic, alpha generation, fitted QRF/ML, paper-trading loop, live
trading, silent auto-rearm.

Trading readiness statement required:

The system is NOT ready for live trading, demo trading, paper trading, or production.

Exact next step: Sequence 07 — PM5 Execution & Broker Routing Layer.
