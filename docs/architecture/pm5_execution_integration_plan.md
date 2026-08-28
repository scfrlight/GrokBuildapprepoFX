# PM5 Execution — Integration Plan (Sequence 07)

Status: **Accepted before implementation**  
Date (UTC): 2026-08-28  
Package: `botmoduleproject1/modules/pm5_execution/`  
Registry name: `pm5_execution` (Sequence 01 stub name, preserved)  
Feature flags:
- `enable_pm5_simulation` (`feature_flags.pm5_simulation`) — test/research env opt-in
- `enable_pm5_execution` (`feature_flags.execution`) — dangerous, YAML false; does **not** open a broker
- `enable_pm5_broker_adapter` — dangerous, Sequence 07 refuses to bind a sender
- `enable_mt5_demo_execution` — future-controlled, always false here
- `enable_live_execution` — hard-blocked

This plan is the pre-implementation gate required by Sequence 07. Implementation
must not begin until this document exists. PM5 is the **execution truth /
OMS-EMS fabric**. It is not a risk brain, not a strategy engine, and not an
MT5 wrapper. `DisabledExecution` remains the default bind.

---

## 1. Position in the pipeline

```text
PM2 RankedCandidate
  → PM3-Strategy Engine TradeIntent
    → PM3 forecasting / QRF ForecastOutput
      → PM4 RiskPublicationBundle   (authoritative admission)
        → PM5 Execution & Broker Routing  (this module)
          → DisabledBrokerAdapter | SimulationBrokerAdapter
            → future MT5 adapter (UNAVAILABLE in Sequence 07)
```

Hard cuts:

- PM4 is the only authorizer. PM5 never accepts PM2 or PM3 artifacts as a submit path.
- `RiskPublicationBundle.execution_permitted` stays **false** (Sequence 06 invariant).
- Simulation may **record** an OMS lifecycle for a PM4 ALLOW/REDUCE bundle.
- Simulation must **not** call a broker, mint a live ticket, or send an `OrderRequest` to MT5.
- `DisabledExecution.submit(OrderRequest)` still raises when the simulation flag is off.
- Live profile remains hard-blocked.

## 2. PM4 → PM5 authorization boundary

Canonical input: `contracts/v1/risk.py::RiskPublicationBundle`.

| Field | PM5 use |
|---|---|
| `verdict.status` | ALLOW required for simulation ingest; DENY/HALT reject |
| `admission.decision` | REJECT/FREEZE/KILL_PROTECTED reject; REDUCE caps quantity |
| `execution_permitted` | always false today → **broker path rejected**; simulation may still shadow-record |
| `sizing.recommended_size` | hard cap; PM5 may only equal or reduce |
| `verdict.recommended_volume` | same cap when set |
| `kill_switch` | latched/tripped → block new submissions |
| `handoff_eligibility` | `eligible_pending_pm5` expected on ALLOW |
| `idempotency_key` | OMS dedup |
| `intent_id` / `event_id` / `correlation_id` / `causation_id` | trace |
| `symbol`, direction via intent/verdict | never flipped |
| `occurred_at` | freshness / no-lookahead |

Reject codes (intake):

`missing_authorization`, `pm4_deny`, `execution_not_permitted` (broker),
`stale_intent`, `lookahead`, `invalid_quantity`, `quantity_exceeds_pm4`,
`unsupported_symbol`, `unsupported_side`, `duplicate_conflict`,
`kill_switch`, `control_blocked`, `schema_mismatch`, `missing_trace`.

PM5 **must not** change: direction, stop/exit constraints, risk budget, strategy id.
PM5 **must not** increase quantity above PM4.

## 3. Simulation / shadow path vs broker path

| Mode | Flag | Adapter | Side effect |
|---|---|---|---|
| `disabled` | all false (YAML default) | none — `DisabledExecution` | `submit` raises |
| `shadow` | simulation off, execution flag on | `DisabledBrokerAdapter` | records blocked; no send |
| `simulation` | `enable_pm5_simulation` | `SimulationBrokerAdapter` | deterministic fake ack/fill; **not** a broker |
| `demo_candidate` | described only | disabled | not enabled |
| `demo_enabled` | future gate | blocked | Sequence 07 refuses |
| `live` | any | hard-blocked | profile refused |

`SimulationBrokerAdapter` produces broker-*like* events (`acknowledged`,
`filled`) with tickets prefixed `SIM-`. Those events are **not** broker truth.
`ReconciliationEngine` in default mode reports `broker_truth=unavailable`,
outcome `degraded` (not `pass` pretending a venue exists).

## 4. Future MT5 adapter boundary

`ems/mt5_adapter.py` exists as a typed placeholder:

- `available() -> False`
- every command returns `BrokerUnavailability` / raises `ExecutionDisabledError`
- no `MetaTrader5` import
- no credentials
- methods documented: placeholder / blocked pending future demo gate

Credentials stay in env names only (`MT5_*` already in PM1 secrets allowlist).
Never logged. Never in git.

## 5. OMS versus EMS

| OMS | EMS |
|---|---|
| Canonical `OrderRecord` | Adapter translation only |
| Lifecycle state machine | submit/cancel/modify/close *requests* |
| Idempotency / dedup | ticket mapping |
| Remaining / filled qty | async ack/fill classification |
| Never talks to a venue | Never allocates risk, never flips side |

Local order state ≠ broker order state ≠ position state ≠ control state ≠ recon state.

## 6. Broker truth reconciliation

When no venue is connected (Sequence 07 default):

- startup recon → `degraded` / `broker_truth_unavailable`
- does **not** silently pass
- does **not** overwrite local history
- new **broker** submissions stay blocked
- simulation fills are tagged `source=simulation` and are not broker truth

When a future adapter reports orders/positions, compare local vs venue,
emit `ReconciliationRecord` (`pass` / `mismatch` / `degraded` / `critical`).
Critical mismatch: block new orders, freeze, alert, require recovery.

Reconnect policy: no immediate new order → fetch truth → reconcile → then
recovery eligibility.

## 7. Independent control plane

Separate from OMS submit path. Usable when EMS is degraded.

Actions: cancel one / group / all, block new, freeze (symbol|strategy|cluster|account|global),
close-only, no-new-risk, emergency cancel, manual review, controlled recovery.

Kill-switch:

- ingest PM4 kill state
- local PM5 latch (reject burst, cancel storm, mismatch, operator)
- no hidden auto-rearm
- recovery requires actor + reason + cooldown

## 8. Disconnect / cancel-on-disconnect

Placeholder policy only. Sequence 07 cannot cancel at a broker because none
is connected. Control plane records `cancel_requested` locally and marks
`broker_cancel=placeholder_pending_adapter`.

## 9. Publication outputs

`ExecutionPublicationBundle` (extends, does not replace, `ExecutionReport`):

- order record + lifecycle events
- control state
- reconciliation snapshot
- exposure truth (local expected vs broker — broker null in default)
- surveillance alerts
- quality metrics (null when insufficient)
- `broker_side_effect=false`
- `mt5_used=false`

Downstream: future PM6. Not a Telegram payload.

## 10. Persistence limitation (before PM7/PM8)

Orders, events, incidents, control, and simulated broker maps live in
`memory://` repositories. Restarts lose execution state. This is **not** a
ledger and must not be presented as one.

## 11. Security / credentials

- No login/password/server in git, logs, diagnostics, or publication bundles.
- Unprefixed env ignored (ADR-006).
- No MT5 package on Linux tests.
- No working broker order in tests.

## 12. Default bind (no-bypass)

| Source | Why it cannot bypass PM4 or open MT5 |
|---|---|
| PM2 / PM3 | no ingest method accepts them |
| CLI | may call ingest; cannot force broker send |
| YAML | flags default false; dangerous flags need env |
| `enable_pm5_execution` | does not bind MT5 |
| Preview / desk | observe-only simulation of *records*, not tickets |
| Test helpers | SimulationBrokerAdapter tickets are `SIM-` |

Deny-by-default:

1. Flags off → `DisabledExecution` (raises).
2. Simulation on, PM4 missing/DENY → reject, no EMS call.
3. Simulation on, ALLOW, `execution_permitted=false` → OMS shadow record, EMS disabled adapter, no venue.
4. Any live profile → refuse process.

## 13. Implementation order (after this plan)

1. Extend `contracts/v1/execution.py` backward-compatibly.
2. Package `modules/pm5_execution/` per Sequence 07 layout.
3. Feature flags + settings + container bind.
4. Tests + traceability.
5. Docs / ADR-012 / README.
6. Architecture desk (observe-only).

Do not claim demo / paper / live / production readiness.
