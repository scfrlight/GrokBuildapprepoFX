# Architecture Baseline — BotModuleProject1

Status: Accepted for Sequence 00; PM1 kernel Sequence 01; config governance Sequence 02; PM2 market context Sequence 03; PM3-Strategy Engine Sequence 04; PM3 forecasting / QRF Sequence 05; PM4 Risk Gate Sequence 06; PM5 Execution Sequence 07; PM6 Post-Trade Sequence 08  
Date (UTC): 2026-08-28  
Scope: EURUSD on MT5 Demo, expandable to additional FX symbols  
Trading readiness: **not ready**. PM3-Strategy Engine emits analytical TradeIntent only. PM3 forecasting / QRF may attach a ForecastOutput envelope. PM4 may ALLOW a risk-governed handoff. That ALLOW is not an order. PM5 may shadow-record an OMS lifecycle in simulation. It does not send to MT5. PM6 may observe PM4/PM5, raise incidents, and plan orderly withdrawal. It does not send orders, size risk, or invent broker truth. No live path is implemented.

This document is the Sequence 00 source of truth for structure, bounded contexts, and safety invariants. Sequence 01 implemented the composition root and v1 contracts against this baseline. Sequence 02 added profiles, pydantic-settings, feature flags, and preflight. Sequence 03 implemented PM2 as a ranking/context layer behind `enable_pm2_market_data` (test/research env opt-in). Sequence 04 implemented the **PM3-Strategy Engine** behind `enable_pm3_strategy_engine` (test/research env opt-in; TradeIntent is not an order). Sequence 05 implemented **PM3 forecasting / QRF** behind `enable_forecasting` (demo/test/research env opt-in; ForecastOutput is not an order; residual quantile envelope, not a fitted QRF). Sequence 06 implemented the **PM4 Risk Gate** behind `enable_pm4_risk_gate` (test/research env opt-in; ALLOW is not an order). Sequence 07 implemented **PM5 Execution** behind `enable_pm5_simulation` (test/research env opt-in; simulation only; `DisabledExecution` default). Sequence 08 implemented **PM6 Post-Trade** behind `enable_pm6_post_trade` (test/research env opt-in; observe-only; `NullMonitoring` default). The module map is unchanged.


## 1. Target monorepo structure

The GitHub repository `scfrlight/GrokBuildapprepoFX` is the durable home of the Python trading system. The Grok App Builder workspace additionally hosts an **architecture console** (`src/`) so operators can inspect the baseline. The console is not a trading module and must not contain order, risk, or broker logic.

```text
GrokBuildapprepoFX / workspace
├── botmoduleproject1/          # Python package (import root)
│   ├── app/                    # PM1 composition root, DI, lifecycle
│   ├── contracts/              # Versioned DTOs, events, ports
│   ├── domain/                 # Pure domain types and invariants
│   ├── application/            # Use-cases / orchestration (no I/O)
│   ├── infrastructure/         # Cross-cutting infra helpers
│   ├── adapters/               # Outbound I/O only
│   │   ├── mt5/
│   │   ├── market/             # synthetic confirmed-bar feed (Sequence 03)
│   │   ├── persistence/
│   │   ├── telegram/
│   │   ├── notifications/
│   │   ├── clock/
│   │   └── filesystem/
│   ├── modules/                # Bounded-context packages
│   │   ├── pm2_market_context/
│   │   ├── pm3_strategy_engine/  # Sequence 04 kernel (flag off)
│   │   ├── pm3_forecasting/      # Sequence 05 kernel (flag off; not a fitted QRF)
│   │   ├── pm4_risk_gate/        # Sequence 06 kernel (flag off; ALLOW ≠ order)
│   │   ├── pm4_risk/             # compatibility re-export of pm4_risk_gate
│   │   ├── pm5_execution/
│   │   ├── pm6_post_trade/       # Sequence 08 kernel (flag off; NullMonitoring default)
│   │   ├── pm6_monitoring/       # compatibility re-export of pm6_post_trade
│   │   ├── pm7_ledger/
│   │   ├── pm8_persistence/
│   │   └── pm9_operator_ux/
│   └── runtime/                # Process host, modes, health
├── configs/                    # Non-secret configuration templates
├── docs/                       # Architecture, ADR, runbooks
├── scripts/bot/                # Operator scripts (no business logic)
├── tests/                      # unit / contract / integration / e2e
├── pyproject.toml
├── requirements.txt
├── .env.example
└── README.md
```

### Grounds for each major directory

| Directory | Why it exists | What it must never contain |
|---|---|---|
| `botmoduleproject1/app` | Composition root for PM1: wiring, registry, lifecycle | Strategy math, risk sizing, MT5 calls |
| `botmoduleproject1/contracts` | Single versioned language between modules | Adapter implementations |
| `botmoduleproject1/domain` | Invariants that do not depend on I/O | Network, files, clocks as wall-clock now() |
| `botmoduleproject1/application` | Use-case orchestration against ports | Concrete MT5 / Telegram / DB clients |
| `botmoduleproject1/infrastructure` | Logging, config loaders, retry/backoff primitives | Trading decisions |
| `botmoduleproject1/adapters` | Replaceable I/O | Domain policy, strategy, risk verdicts |
| `botmoduleproject1/modules` | One folder per PM bounded context | Cross-module imports that skip contracts |
| `botmoduleproject1/runtime` | Process modes, health, halt | Business rules |
| `configs` | Public, reviewable parameters | Secrets, account IDs, tokens |
| `docs` | Architecture and operator knowledge | Credentials |
| `tests` | Proof of contracts and safety gates | Live broker calls by default |
| `src` (App Builder only) | Architecture console preview | Trading execution |

Python composition root lives at `botmoduleproject1/app`, not workspace-root `app/`, so it cannot collide with the web bundler's historical `app/` router convention.

## 2. Bounded contexts

| Context | Package | Responsibility |
|---|---|---|
| Platform / bootstrap | `app` + `runtime` (PM1) | Composition root, DI, lifecycle, registry, health, config contracts |
| Market context | `modules/pm2_market_context` (PM2) | Universe scan, regime, confluence, ranking, suppression, publication. No orders. |
| PM3-Strategy Engine | `modules/pm3_strategy_engine` | Templates, profiles, registry, symbol pipes, consensus, TradeIntent (Sequence 04 kernel, flag off) |
| Forecasting | `modules/pm3_forecasting` (PM3 forecasting / QRF) | Residual quantile envelope, ForecastOutput, conformal coverage (Sequence 05 kernel, flag off). Not the Strategy Engine. Not a fitted QRF. |
| Risk | `modules/pm4_risk` (PM4) | Allocation, sizing, heat, drawdown governor, kill-switch. **Sole final gate** |
| Execution | `modules/pm5_execution` (PM5) | OMS/EMS simulation, independent control, recon (degraded without venue). No MT5 send. |
| Surveillance | `modules/pm6_post_trade` (PM6; registry `pm6_monitoring`) | Post-trade controls, two defence lanes, incidents, governance. Observe-only. |
| Ledger / evidence | `modules/pm7_ledger` (PM7) | Trade ledger, evidence, replay, reporting |
| Persistence / recovery | `modules/pm8_persistence` (PM8 + PM8a spec) | CQRS, outbox/inbox, idempotency, snapshots, reconciliation |
| Operator UX | `modules/pm9_operator_ux` (PM9 + PM9a) | Telegram control plane and fine-tune studio |

PM8a is a build-spec, not a runtime bounded context. PM9a lives inside the operator UX context.

## 3. Allowed dependency direction

Dependencies point **inward** toward domain and contracts.

```text
adapters  →  infrastructure  →  application  →  domain
     \            |                 |             ↑
      \           |                 └→ contracts ←┘
       \          └→ contracts
        └→ contracts

modules/*  →  contracts, domain, application ports
app/runtime  →  modules via interfaces, never via adapter internals
```

Rules:

1. Domain depends on nothing outside the standard library and `contracts` value types.
2. Application depends on domain + ports defined in `contracts`.
3. Adapters implement ports. They may use infrastructure.
4. Modules may call other modules only through `contracts` (events/DTOs/ports).
5. `app` (composition root) is the only place that constructs concrete adapters.

## 4. Forbidden dependencies

| From | To | Why forbidden |
|---|---|---|
| `adapters/mt5` | `modules/pm3_strategy_engine`, `pm4_risk` | Broker adapter must not contain strategy/risk logic |
| `adapters/telegram` | any trading module internals | Transport must not contain trading business logic |
| `modules/pm5_execution` | `modules/pm3_*` | Execution must not generate intents |
| `modules/pm3_strategy_engine` | `modules/pm5_execution` | Intents never skip the risk gate |
| `modules/pm3_forecasting` | `modules/pm5_execution` | Forecasts are enrichment, not orders |
| `modules/pm9_operator_ux` | `adapters/mt5` | Operator UX talks to application ports |
| Any module | persistence tables directly | Persistence API is the only durable path (PM8) |
| Any module | naive `datetime` / local TZ | UTC-first policy |
| Tests / docs / logs | real secrets | Configuration governance |

## 5. Future integration map (PM1–PM9a)

| Sequence | Deliverable | Integrates through |
|---|---|---|
| 01 / PM1 | Contract-first domain foundation, composition root | `contracts`, `app`, `runtime` |
| PM2 | Market data + session + regime | `MarketSnapshot`, `SessionContext`, `RegimeState` |
| PM3-Strategy Engine | TradeIntent production (Sequence 04 kernel; not an order) | `TradeIntent` / `NoTradeDecision` |
| PM3 forecasting / QRF | Enrichment of intents (Sequence 05 kernel; not an order) | `ForecastOutput` linked by `intent_id`; never mutates side |
| PM4 | RiskVerdict | Exclusive permission object consumed by PM5 |
| PM5 | Execution | Accepts only `(TradeIntent, RiskVerdict=ALLOW)` |
| PM6 | Monitoring | Observes PM4/PM5 publications; never orders; never invents broker truth |
| PM7 | Ledger/evidence | Append-only via PM8 persistence API |
| PM8 / PM8a | Persistence + recovery | Repositories, outbox, snapshots |
| PM9 / PM9a | Operator UX | Commands → application ports; never adapters |

## 6. Layer boundaries

| Layer | Location | Allowed to do | Must not do |
|---|---|---|---|
| Domain | `domain/` | Invariants, value objects, state machines | I/O |
| Application | `application/` | Use-cases, policy orchestration via ports | Construct adapters |
| Infrastructure | `infrastructure/` | Logging, config parse, retries | Decide trades |
| Adapters | `adapters/` | Talk to MT5, DB, Telegram, FS, clock | Own strategy/risk |
| Contracts | `contracts/` | Versioned schemas, ports, events | Implementations |
| Runtime | `runtime/` | Modes, health, halt, process host | Business rules |
| Persistence | `modules/pm8_persistence` + `adapters/persistence` | Durable access | Bypass by other modules |
| Tests | `tests/` | Prove contracts and safety | Default-live broker |

## 7. Architectural invariants

1. **Broker adapter contains no strategy or risk logic.**
2. **Telegram transport contains no trading business logic.** Commands are messages; application services interpret them.
3. **Only the PM4 risk gate issues a final execution permission.** PM5 must refuse any order without a positive `RiskVerdict`.
4. **Persistence API is the single path for durable data.** No module writes its own SQLite/JSON ledger as a side channel after PM8 exists.
5. **Inter-module messages carry identity fields** where applicable: `event_id`, `correlation_id`, `causation_id`, `idempotency_key`.
6. **UTC-first.** All timestamps are timezone-aware UTC, serialized as ISO-8601. Naive datetimes are a defect.
7. **Demo-first, live-disabled.** `TRADING_MODE=demo`, `LIVE_TRADING_ENABLED=false`. Live CLI is recognized and rejected until a future evidentiary waiver.
8. **Safe halt / observe-only** on unknown state, config error, stale data, connection failure, incomplete recovery, or ledger inconsistency.
9. **No secrets in source, logs, tests, or documentation.**
10. **No trading operation is possible without a positive risk verdict** — even when the risk engine is not yet implemented, the invariant is reserved in contracts.

## 8. Safety posture (Sequence 00)

The process host, when it exists, must start in a non-executing mode. Until PM1+PM4+PM5+PM8 recovery exist, the only honest runtime is **observe-only / live-disabled**.

This baseline does **not** authorize:

- demo order sending
- paper order sending
- live trading
- MT5 connections
- Telegram bots
- schema migrations
- ML training

Next authorized step: **Sequence 01 — Contract-First Domain Foundation / PM1**.
