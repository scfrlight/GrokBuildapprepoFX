# ADR-013: PM6 post-trade governance

- Status: Accepted
- Date: 2026-08-28
- Sequence: 08
- Supersedes: none (extends ADR-011, ADR-012)

## Context

PM4 is the exclusive risk gate. PM5 is the OMS/EMS fabric (simulation/shadow in
Sequence 07). Neither is a continuous post-trade control layer. Sequence 08
adds PM6 as monitoring, surveillance, incidents, and governance intelligence.

## Decision

1. **Observe-only authority.** PM6 consumes PM4 and PM5 publications. It never
   sizes risk, never submits, never calls MT5, never fabricates broker truth.
2. **Two lines of defence.** Operator lane and independent control lane share
   events but keep separate summaries, priorities, and recommended actions.
3. **Truth provenance.** `SIM-*` is `simulation_truth`. No venue → recon stays
   `degraded`. Labelling simulation as broker truth is a critical incident.
4. **Incident lifecycle.** Detected → … → closed or transferred. No silent
   disappearance. Suppression requires a reason and retains evidence.
5. **Withdrawal is a plan.** PM6 may request PM5 control actions. Completion
   requires confirmation. No auto-rearm.
6. **Non-durable.** In-memory until PM7. `persistence_handoff=non_durable_before_pm7`.
7. **Feature flags.** `enable_pm6_post_trade` and sub-flags are requires-review,
   YAML false, test/research env opt-in. Default bind remains `NullMonitoring`.

## Consequences

- Composition root binds `PM6PostTradeModule` only when the master flag is on.
- Tests must prove no orders, no MT5, no broker truth, degraded recon, lanes.
- Sequence 09 (PM7) is the first durable evidence store.

## Alternatives considered

1. Fold surveillance into PM5 — rejected; PM5 is execution truth, not governance.
2. Auto-complete withdrawal after N seconds — rejected.
3. Treat degraded recon as pass in simulation — rejected.
