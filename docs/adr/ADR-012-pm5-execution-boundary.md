# ADR-012: PM5 Execution boundary

- Status: Accepted
- Date: 2026-08-28
- Sequence: 07
- Supersedes: none (extends ADR-007, ADR-011)

## Context

Sequence 06 made PM4 the exclusive risk gate. `RiskPublicationBundle.execution_permitted`
is frozen false. Sequence 07 must introduce an OMS/EMS fabric without opening a
broker, MT5 session, paper loop, or live path. `DisabledExecution` remains the
default bind.

## Decision

1. **PM4-only authorization.** PM5 `ingest` accepts only `RiskPublicationBundle`.
   PM2/PM3 artifacts have no submit path. Missing authorization, PM4 DENY /
   FREEZE / KILL_PROTECTED reject. PM5 cannot increase quantity, flip side,
   or allocate risk.
2. **OMS / EMS separation.** OMS owns canonical `OrderRecord`, lifecycle,
   idempotency, remaining quantity. EMS adapters only translate. Simulation
   tickets are `SIM-*` and are not broker truth.
3. **Broker truth precedence.** When a venue is absent (Sequence 07 default),
   reconciliation is `degraded` / `broker_truth_unavailable`, never a silent
   pass. Critical mismatch (when a venue exists) blocks new orders.
4. **Independent control plane.** Freeze, close-only, no-new-risk, emergency
   cancel, and recovery are usable when EMS is degraded. Kill-switch latches.
   **No hidden auto-rearm.** Recovery needs actor + reason + cooldown.
5. **Simulation-first.** `enable_pm5_simulation` (test/research env opt-in)
   binds `PM5ExecutionModule` + `SimulationBrokerAdapter`.
   `enable_pm5_execution` does not open a broker. Broker / MT5 / live flags
   are refused. `submit(OrderRequest)` always raises.
6. **Reconnect reconciliation.** New broker submissions are ineligible until
   broker truth is fetched and reconciled. Sequence 07 cannot fetch a venue,
   so the operating state stays degraded.
7. **In-memory only.** Orders, events, incidents, and control state live in
   `memory://` until PM7/PM8. Restarts lose execution state. This is not a
   ledger.

## Consequences

- Flags off → `DisabledExecution`.
- Simulation may shadow-record a PM4 ALLOW/REDUCE even while
  `execution_permitted=false`. The broker path still rejects.
- Tests must prove no `MetaTrader5` import, no live profile, no PM4 bypass.
- Sequence 08 (PM6) consumes execution publications; it still cannot trade.

## Alternatives considered

1. Bind MT5 behind `enable_pm5_execution` in demo — rejected.
2. Treat simulation fills as recon `pass` — rejected; that fabricates venue truth.
3. Auto-rearm after cooldown — rejected.
