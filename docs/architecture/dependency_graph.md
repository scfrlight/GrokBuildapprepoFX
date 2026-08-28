# Dependency Graph — BotModuleProject1

Status: Accepted for Sequence 00; PM7 Persistence producer live in Sequence 09 (flag off, append-only, NullLedger default)  
Date (UTC): 2026-08-28

## 1. Canonical data flow

```text
Market Data
  → Session / Regime
  → PM2 Confluence / Rank (PublicationBundle)
  → Signal
  → PM3-Strategy Engine TradeIntent
  → Forecast / QRF Enrichment
  → PM4 Risk Verdict
  → PM5 Execution
  → PM6 Post-Trade / Surveillance / Incidents
  → PM7 Persistence / Journal / Evidence
  → PM8 Persistence API
  → PM9 Operator UX
```

Hard cuts in this flow:

- A `Signal` is not an order.
- A `RankedCandidate` is not an order.
- A `TradeIntent` is not an order.
- A forecast does not create or mutate an intent's side; it only enriches uncertainty fields.
- PM5 is unreachable without `RiskVerdict.status == ALLOW`.
- A PM5 simulation fill is not broker truth.
- PM6 observes; it does not authorize, size, or submit.
- Reconciliation without a venue stays degraded — never a silent pass.
- Persistence is append-only; committed records are immutable; corrections are new events.
- `SIM-*` remains simulation truth even when journaled.
- Operator UX observes and issues *commands to application ports*, never raw broker calls.

## 2. Module I/O table

| Module | Inputs | Outputs | Depends on | Criticality | Failure types |
|---|---|---|---|---|---|
| PM1 platform | Config, clock, env | Process, registry, health | contracts, runtime | Startup-critical | Config error → halt |
| PM2 market context | Synthetic/broker bars, calendar | PublicationBundle (shortlist/watchlist/suppressed), RankedCandidate, regime | contracts, synthetic feed (MT5 adapter later) | Ready-critical (non-fatal if flag off) | Stale data → no shortlist; observe-only |
| PM3-Strategy Engine | Snapshot, regime, profiles, RankedCandidate | TradeIntent / NoTradeDecision (shadow; no lot size) | contracts, PM2 public outputs | Decision-critical (non-fatal if flag off) | Invalid profile / stale / handoff-false → NoTradeDecision |
| PM3 forecasting / QRF | Intent, confirmed synthetic bars | ForecastOutput (quantiles, model version; not an order) | contracts, synthetic feed, in-memory registry | Degraded-ok (non-critical) | Insufficient history / lookahead → None; risk must still fail closed |
| PM4 risk gate | Intent, forecast, ranked candidate, book placeholders | RiskVerdict + RiskPublicationBundle (not an order) | contracts, in-memory control state | Execution-critical | Any doubt → DENY / HALT; ALLOW still pending PM5 |
| PM5 execution | RiskPublicationBundle | ExecutionPublicationBundle (simulation; not a broker order) | contracts, PM4, in-memory OMS | Execution-critical (non-fatal if flag off) | No venue → recon degraded; submit() raises |
| PM6 post-trade | ExecutionPublicationBundle, RiskPublicationBundle | OperationalTruthBundle (observe-only; not an order) | contracts, PM4, PM5, in-memory evidence | Ops-critical (non-fatal if flag off) | No venue → monitoring ≥ degraded; never fabricate broker truth |
| PM7 ledger | PM4/PM5/PM6 publications, LedgerEvent | PersistencePublicationBundle, evidence, replay (not an order) | contracts, in-memory/file/sqlite journal | Recovery-critical (non-fatal if flag off) | Integrity mismatch → compromised; never rewrite; production_durable refused |
| PM8 persistence | All durable writes | Repositories, snapshots, outbox | DB adapter | Recovery-critical | Incomplete recovery → halt |
| PM9 operator UX | Commands, queries | Operator views, command receipts | application ports | Ops-non-fatal | Transport down → local observe-only |
| PM9a studio | Research artifacts | Parameter proposals | PM9, contracts | Research-only | Never auto-promotes to live |

## 3. Contracts required in Sequence 01

These names are reserved. Sequence 01 must introduce versioned schemas (v1) without implementing producers/consumers beyond PM1 host wiring.

| Contract | Purpose |
|---|---|
| `EventEnvelope` | `event_id`, `correlation_id`, `causation_id`, `idempotency_key`, UTC `occurred_at` |
| `RuntimeMode` | test / doctor / backtest / research / demo / paper / observe-only / live-disabled |
| `HealthStatus` / `Readiness` / `Liveness` | Startup vs ready vs live probes |
| `ConfigSnapshot` | Redacted public config + secret-ref names only |
| `ClockPort` | Injected UTC clock; no naive datetime |
| `MarketSnapshot` | Symbol, bid/ask, stamps, staleness |
| `SessionContext` | FX session membership |
| `RegimeState` | Regime label + confidence + as-of |
| `Signal` | Pre-intent indication |
| `TradeIntent` | Desired side/size hypothesis from PM3-Strategy Engine |
| `ForecastEnvelope` | QRF/uncertainty payload |
| `RiskVerdict` | ALLOW / DENY / HALT with reasons; exclusive execution permission |
| `OrderCommand` | Execution request, valid only with ALLOW verdict reference |
| `FillEvent` / `PositionSnapshot` | Execution results |
| `LedgerEntry` | Evidence record |
| `RecoveryCheckpoint` | Recovery cursor / snapshot pointer |
| `OperatorCommand` | PM9 command envelope |
| `SafeHaltReason` | Why the host entered halt / observe-only |

## 4. Dependency inversion rules

1. High-level modules (`pm3_strategy_engine`, `pm4_risk`) must not import adapters.
2. Ports live in `contracts` (or domain if purely business). Adapters implement them.
3. Composition root (`app`) binds ports to adapters at process start.
4. Events, not direct calls, cross bounded-context boundaries after PM1.
5. Read models for PM9 go through PM8 query side, not PM5 internals.
6. Tests bind fakes; production binds adapters. No adapter is a singleton imported by domain.

## 5. Future adapter boundaries

| Adapter | Port (future) | Constraint |
|---|---|---|
| MT5 | `BrokerGateway` | Quotes, orders, positions, account. No strategy/risk. Demo-only default. |
| PostgreSQL | `PersistenceGateway` | Sole durable store after PM8. |
| Telegram | `OperatorTransport` | Encode/decode messages only. |
| Filesystem | `ArtifactStore` | Models, reports, snapshots as blobs. |
| Clock / scheduler | `ClockPort`, `SchedulerPort` | Deterministic in tests. |
| Model registry | `ModelRegistryPort` | Versioned artifacts; no training in adapter. |
| Notifications | `AlertPort` | Fire-and-forget alerts; cannot authorize trades. |

## 6. Cycle prohibitions

Illegal cycles (must fail review):

```text
pm5_execution → pm3_strategy_engine
pm3_strategy_engine → pm5_execution
adapters.mt5 → pm4_risk
adapters.telegram → pm5_execution
pm9_operator_ux → adapters.mt5
pm7_ledger → adapters.mt5
```

Legal:

```text
pm5_execution → contracts.RiskVerdict
pm4_risk → contracts.TradeIntent (read)
pm8_persistence ← all modules (write/read via API)
pm6_monitoring ← events
pm9_operator_ux → application command ports
```
