# ADR-011: PM4 Risk Gate governance

- Status: Accepted
- Date: 2026-08-28
- Sequence: 06
- Supersedes: none (extends ADR-007)

## Context

ADR-007 established that PM4 is the only issuer of a final `RiskVerdict` and that
PM5 may not bind an order without `status=ALLOW`. Sequence 00–05 left PM4 as
`NullRiskGate` (always DENY). Sequence 06 implements the gate as a capital-
preservation module sitting after PM2 + PM3-Strategy Engine + PM3 forecasting
and before a still-closed PM5.

## Decision

1. **Deny-by-default ownership.** No TradeIntent may pass toward execution
   without an explicit PM4 ALLOW. Missing, stale, malformed, lookahead, or
   schema-incompatible PM2/PM3 artifacts DENY. Empty forecast validity
   diagnostics DENY.
2. **Risk-governed handoff boundary.** PM4 publishes `RiskPublicationBundle`.
   That object is not an `OrderRequest`. `execution_permitted` is frozen false
   for Sequence 06. ALLOW means “admitted for a future PM5”, not “send”.
3. **Drawdown ladder.** Stages `normal → mild_throttle → reduced_risk →
   restricted_risk → freeze → kill_protected` (plus `recovery`). Throttle
   factors are applied to the whole budget tree, not as a flat lot tweak.
4. **Kill-switch scope model.** Scopes: symbol / strategy / cluster / account.
   Tripped switches latch. Recovery requires actor + reason + cooldown.
   **No hidden auto-rearm.**
5. **Non-durable in-memory control state.** Heat, drawdown, kill, incidents, and
   inventory live in `memory://` repositories until PM7/PM8. Restarts lose
   control state. This must not be presented as a ledger.
6. **Feature flag.** `enable_pm4_risk_gate` is requires-review, YAML false,
   env opt-in, **test and research only**. Demo/live cannot open an execution
   path. Even when enabled, `DisabledExecution` still raises.

## Consequences

- Composition root binds `PM4RiskGateModule` only when the flag is on;
  otherwise `NullRiskGate` remains.
- Tests must prove ALLOW does not call PM5 and does not construct orders.
- Sequence 07 (PM5) is the first module allowed to consume ALLOW verdicts for
  routing — still behind its own dangerous flag.

## Alternatives considered

1. Flat percent-of-equity lot calculator — rejected; not a risk gate.
2. Auto-rearm kill-switch after N minutes — rejected.
3. YAML-enable in demo — rejected; demo must not look trade-ready.
