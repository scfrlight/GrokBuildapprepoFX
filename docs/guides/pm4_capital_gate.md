# PM4 capital-management gate

Canonical home: **Sequence 06 / `pm4_risk_gate`**.  
Historical Master Orchestration title: “Sequence 07 — PM5 Risk & Capital Management Gate”.

This is **not** a competing PM5 package. Canonical Sequence 07 remains `pm5_execution` (OMS/EMS, `SIM-*` only). Do not create `pm5_risk_capital_gate`.

## What it is

`PM4RiskGateModule.evaluate_capital(RiskEvaluationRequest)` runs forty independent
checks, sizes with `Decimal` (never float, never round up through a limit),
persists via `PersistenceApiV1`, and emits either:

- `RiskApprovedExecutableIntent` with **`execution_allowed=false`**, `creates_order=false`, or
- `RiskRejection`

An approved executable intent is **not** an order. `execution_permitted` and
`trading_readiness` cannot be true on `RiskDecision`.

Existing `evaluate()` / `evaluate_intent()` paths are unchanged. PM4 remains the
exclusive risk gate (ADR-007).

## Checks (always all 40)

See `botmoduleproject1/modules/pm4_risk_gate/capital/catalog.py`. Missing data is
`block`, never a silent pass. Unknown reconciliation, unknown exposure, unknown
account, and persistence down fail closed.

## Persistence

One database: PM8 `PersistenceApiV1`. Event types:

- `risk.decision.committed` (family AUDIT)
- `risk.drawdown.snapshot` (restart-safe peak / daily loss)
- `risk.replay.divergence` (do not overwrite)

Idempotency: same key + same hash → stored result. Same key + different hash →
conflict, not approval.

## Safe-halt

Drawdown freeze and system blocks trip a latch. Recovery requires a non-automatic
actor. `auto_rearm` stays false.

## Safety locks (unchanged)

- Live CLI fail-closed
- Telegram Bot API unbound
- `/buy` REFUSED
- MT5 terminal not enabled
- Sequence 15+ blocked
- `production_durable` still refused even when PostgreSQL is present

## Viewer

The App Builder ops console shows exported JSON from
`public/observability/pm4_capital_gate.json`. It is not a trading UI.
