# PM5 — Execution & Broker Routing (Sequence 07)

OMS/EMS fabric after PM4. Simulation and shadow only.

- Accepts only `RiskPublicationBundle`.
- Default bind is `DisabledExecution` (`submit` raises).
- `enable_pm5_simulation` (test/research env) binds this module + `SimulationBrokerAdapter`.
- Tickets are `SIM-*` and are **not** broker truth.
- Reconciliation without a venue is `degraded`, never a silent pass.
- MT5 adapter is a blocked placeholder. No `MetaTrader5` import.
- `execution_permitted` stays false; the broker path rejects.
- In-memory only. Not a ledger.

The system is NOT ready for live trading, demo trading, paper trading, or production.
