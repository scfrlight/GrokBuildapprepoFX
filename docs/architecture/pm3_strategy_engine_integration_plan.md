# PM3-Strategy Engine — Integration Plan (Sequence 04)

Status: Accepted before implementation  
Date (UTC): 2026-08-28  
Package: `botmoduleproject1.modules.pm3_strategy_engine`  
Display name: **PM3-Strategy Engine** (never shortened to “PM3”)

This plan is the gate for Sequence 04. Implementation follows it; it does not authorize trading.

---

## 1. Naming collision

| Name | Package | Owns | Must not own |
|---|---|---|---|
| **PM3-Strategy Engine** | `modules.pm3_strategy_engine` | templates, profiles, pipes, consensus, TradeIntent, NoTradeDecision, strategy health | QRF, quantiles, forecasts |
| **PM3 forecasting / QRF** | `modules.pm3_forecasting` | future predictive models | strategy votes, TradeIntent |

Kernel placeholders stay distinct: `NullSignals` (this module) vs `NullModel` (`pm3_forecasting`). Comments, class names, variables, docs, and the Sequence 04 report always write **PM3-Strategy Engine**.

---

## 2. Inputs (from PM2 only via public contracts)

Consumed through `IPM2ContextAdapter`. No imports of PM2 private engines, scanners, or feature builders.

| Contract | Owner | Use |
|---|---|---|
| `PublicationBundle` | `contracts.v1.pm2` | scan-level handoff |
| `RankedCandidate` | `contracts.v1.pm2` | per-symbol evaluation input |
| `CandidateContextSnapshot` | `contracts.v1.pm2` | regime, session, data quality, families |
| `CandidateScoreCard` | `contracts.v1.pm2` | scores / vetoes / tier |
| `CandidateQualificationState` | `contracts.v1.pm2` | STALE / SUPPRESSED gates |
| `RegimeState` / `RegimeType` / `SessionContext` | `contracts.v1.session` | regime routing |
| `FeatureSnapshot` (strategy-side view) | this module, adapted | template evidence, not PM2 internals |

Placeholders (read-only, never approval):

- `PortfolioContext`, `RiskContext`, `ExecutionContext`, `SystemFlags`

Presence of `RiskContext` is **not** a RiskVerdict and must not be treated as ALLOW.

---

## 3. Outputs (domain artifacts only)

| Artifact | Downstream | Forbidden use |
|---|---|---|
| `StrategyVote` | consensus | not an order |
| `SymbolConsensusResult` | intent service | not permission |
| `TradeIntent` | future PM3 forecasting, then PM4 | not `OrderRequest`; no lot size |
| `NoTradeDecision` | observe-only path | not a veto of PM4 (PM4 still exclusive) |
| `ProfileHealthSnapshot` / `TrackerSnapshot` / `StrategyDiagnostics` | PM9 later | not Telegram payloads yet |

Canonical v1 types stay in `contracts.v1.strategy` (`TradeIntent`, `ExitPlan`, `Direction`, `EntryType`, `ConsensusDecision`, `NoTradeDecision`). Sequence 04 extends them backward-compatibly. `requested_volume` remains on `TradeIntent` for v1 compatibility and **must stay `None`** — it is not lot size and is never populated.

---

## 4. Event flow

```text
PM2 PublicationBundle / RankedCandidate
  → IPM2ContextAdapter (public contracts only)
  → GlobalSystemPipe (flags, observe-only, no account risk)
  → SymbolPipe (max 3 active branches)
       → IStrategyTemplate.evaluate → StrategyVote | abstain
       → ICalibrationPolicy
       → IConsensusPolicy → GO_LONG | GO_SHORT | WAIT | NO_TRADE
       → IntentService → TradeIntent | NoTradeDecision
  → IStrategyEventPublisher (in-memory / journal hook)
  → FeedbackPipe (synthetic outcomes → tracker/health)
```

Hard cuts:

```text
PM3-Strategy Engine  ─X→  PM5 execution
PM3-Strategy Engine  ─X→  adapters.mt5
PM3-Strategy Engine  ─X→  Telegram
TradeIntent          ─X→  OrderRequest
Forecast             ─X→  TradeIntent side mutation (future PM3 forecasting enriches only)
```

Legal future path:

```text
PM2 context → PM3-Strategy Engine TradeIntent
  → PM3 forecasting/QRF enrichment
  → PM4 RiskVerdict ALLOW
  → PM5 Execution
```

---

## 5. Dependency direction

```text
pm3_strategy_engine
  → contracts.v1 (strategy, pm2, session, time, identity, journal, tuning)
  → app.capabilities / app.health (manifest + checks only)
  ─X→ modules.pm4_risk internals
  ─X→ modules.pm5_execution
  ─X→ adapters.mt5
  ─X→ adapters.telegram
  ─X→ modules.pm3_forecasting
  ─X→ PM2 private packages (engines, scanner, features)
```

PM1 `container.py` is the only binder. Flag off → `NullSignals`. Flag on (test/research env opt-in) → `PM3StrategyEngineModule`.

---

## 6. Contract ownership

| Contract | Owner | Sequence 04 action |
|---|---|---|
| `TradeIntent` / `ExitPlan` / `NoTradeDecision` | PM3-Strategy Engine (v1) | extend, do not fork |
| `ParameterSchema` | `contracts.v1.tuning` | reuse |
| PM2 ranked types | PM2 | consume only |
| `RiskVerdict` | PM4 | do not produce |
| `OrderRequest` | PM5 | do not produce |
| `ForecastOutput` | PM3 forecasting | do not produce |

---

## 7. Degraded / fail-closed behaviour

| Condition | Result |
|---|---|
| Feature flag off | `NullSignals`; no votes, no intents |
| PM2 `handoff_eligibility=false` and policy requires handoff | shadow diagnostics allowed; **NoTradeDecision** |
| Stale / incomplete / malformed / lookahead | NoTradeDecision or abstain |
| Untradeable / incompatible regime | template abstain; consensus WAIT/NO_TRADE |
| Disabled / degraded / retired profile | vote dropped |
| Duplicate `idempotency_key` | no second intent |
| System flag forbids evaluation | no evaluation |
| Missing / invalid profile version | NoTradeDecision |
| Close long/short probabilities or conflict | WAIT or NO_TRADE |
| Live profile | already refused at Settings |
| Any unknown state | observe-only / NoTradeDecision |

Shadow operating mode is the default. Activation of a profile version is **strategic activation in observe-only**, not permission to trade.

---

## 8. Persistence

Sequence 04 uses in-memory repositories behind ports (`IProfileRepository`, `IVersionRepository`, `IBindingRepository`, `ITrackerRepository`). They are not durable and must not be described as PM8. PM7/PM8 may replace them later without changing application services.

---

## 9. Feature flag

| Flag | Safety | Default | Allowed profiles |
|---|---|---|---|
| `enable_pm3_strategy_engine` | requires-review | false | test, research |

YAML stays false. Env: `BOTMODULEPROJECT1_FEATURE__ENABLE_PM3_STRATEGY_ENGINE=true` (alias `…ENABLE_STRATEGY_ENGINE`). Demo/backtest/live cannot opt in. Opt-in does not add execution capability.

---

## 10. Out of scope (Sequence 04)

QRF/ML, risk math, lot sizing, MT5, orders, fills, schema/migrations, Telegram, live/paper execution, external market APIs.
