# PM4 Risk Gate — Integration Plan (Sequence 06)

Status: **Accepted before implementation**  
Date (UTC): 2026-08-28  
Package: `botmoduleproject1/modules/pm4_risk_gate/`  
Registry name: `pm4_risk` (backward-compatible with Sequence 01 stubs)  
Feature flag: `enable_pm4_risk_gate` (`feature_flags.risk_engine`)

This plan is the pre-implementation gate required by Sequence 06. Implementation
must not begin until this document exists. PM4 is the **authoritative pre-trade
capital-protection layer**. It is not a signal engine, not a forecast, not a
broker, and not an order factory.

---

## 1. Position in the pipeline

```text
PM2 RankedCandidate / PublicationBundle
  → PM3-Strategy Engine TradeIntent
    → PM3 forecasting / QRF ForecastOutput
      → PM4 Risk Gate  (this module)
        → RiskPublicationBundle + RiskVerdict
          → future PM5 Execution  (CLOSED in Sequence 06)
```

Hard cuts:

- PM2 ranks. It does not size, admit, or execute.
- PM3-Strategy Engine emits analytical `TradeIntent` only. `requested_volume` is always `None`.
- PM3 forecasting / QRF attaches a residual quantile envelope. It does not flip side or size.
- **PM4 is the only module allowed to convert analytical intent into a risk-governed handoff.**
- PM5 is not implemented. `DisabledExecution.submit` still raises. ALLOW is not an order.

## 2. Exact upstream inputs

### From PM2 (`contracts/v1/pm2.py`)

| Field | Use in PM4 |
|---|---|
| `candidate_id` | intake identity, trace |
| `symbol` | must match intent and forecast |
| `as_of` | freshness / no-lookahead |
| `context` (regime, sessions, data_quality, feature families) | admission + liquidity + session |
| `scorecard` (quality_tier, liquidity_score, correlation_penalty, confluence) | admission + sizing discounts |
| `state` (qualification state machine) | STALE / SUPPRESSED / INVALIDATED → DENY |
| `correlation_cluster` | concentration / one-per-cluster |
| `handoff_eligibility` | hard veto when false |
| `final_rank` / `side_bias` | diagnostics only; never a side flip |
| `timing_valid_until` | stale if clock > expiry |
| `event_id` / `correlation_id` | trace |

Missing, stale, malformed, schema-incompatible, or lookahead PM2 artifacts → **DENY**.

### From PM3-Strategy Engine (`contracts/v1/strategy.py`)

| Field | Use in PM4 |
|---|---|
| `intent_id` / `idempotency_key` | identity, duplicate suppression |
| `source_candidate_id` | must equal PM2 `candidate_id` when both present |
| `symbol`, `occurred_at` / `created_at` | freshness, symbol consistency |
| `direction`, `entry_type` | admission, collars; **never mutated** |
| `entry_zone_low` / `entry_zone_high` / `entry_price` | stop-distance basis, price collar |
| `exit_plan.stop_price` / `stop_loss` | required for sizing; missing stop → DENY |
| `confidence_score` / `setup_quality` / `consensus_score` | quality factor |
| `regime_state`, `urgency_class`, `signal_expiry` | session / stale |
| `profile_id` / `version_id` | sleeve budget key |
| `diagnostics` | audit only |
| `event_id` / `correlation_id` / `causation_id` | trace |

PM4 does not generate alpha and does not change `direction` to “improve” outcomes.

### From PM3 forecasting / QRF (`contracts/v1/forecasting.py`)

| Field | Use in PM4 |
|---|---|
| `forecast_id` / `intent_id` | `intent_id` must match TradeIntent |
| `symbol`, `occurred_at` | consistency + freshness |
| `quantiles` (q05…q95) | interval width, uncertainty discount |
| `coverage` / `sample_size` / `horizon_bars` | predictive-quality factor |
| `diagnostics` | **required validity evidence**; empty diagnostics → DENY |
| `model` | inventory / audit |

Missing forecast, empty validity diagnostics, lookahead flags, or schema mismatch → **DENY**.
PM4 does not train, fit, or mutate the envelope.

### Book-state placeholders (in-memory, not PM7/PM8)

| Placeholder | Role |
|---|---|
| account equity / currency | baseline risk dollars |
| open exposure snapshot | raw + effective heat |
| pending-order placeholder | burst / duplicate / notional caps |
| drawdown state | throttle ladder |
| kill-switch state | last-safeguard |
| portfolio heat state | residual headroom |

These are **not** a durable ledger. Persistence expectations are in §8.

## 3. Exact downstream outputs toward PM5

Canonical objects live in `contracts/v1/risk.py` (extended, not duplicated):

| Artifact | Meaning |
|---|---|
| `RiskVerdict` | exclusive ALLOW / DENY / HALT permission object (ADR-007) |
| `RiskAdmissionCard` | approve / reduce / reject / freeze / kill_protected |
| `RiskBudgetCard` | hierarchical budgets + residual headroom |
| `PositionSizingDecision` | recommended size + every discount factor + rationale |
| `PortfolioHeatCard` | raw / effective / cluster / directional / session heat |
| `ConcentrationExposureCard` | FX overlap, crowding, stressed concentration |
| `DrawdownStateCard` | stage, peak-to-trough, streak, freeze |
| `PreTradeControlDecision` | fat-finger, collar, burst, route eligibility |
| `KillSwitchState` | scope, trigger, cancel-intent, recovery eligibility |
| `RiskPublicationBundle` | immutable handoff envelope wrapping the cards + verdict |

**Critical boundary**

- PM4 output is a **risk-governed handoff artifact**, not a broker order.
- PM4 **must not** construct `OrderRequest`, `ExecutionReport`, or any MT5 object.
- `RiskVerdict.status == ALLOW` still does **not** call PM5.
- `HandoffEligibility` on ALLOW is `eligible_pending_pm5`. Execution remains closed.
- `execution_permitted` on the bundle is **always false** in Sequence 06.

PM5 (future) is the only consumer allowed to bind `OrderRequest.risk_verdict_id`
to an ALLOW verdict. Sequence 06 leaves that path unimplemented.

## 4. No-bypass rule (deny-by-default gate ownership)

PM4 owns the gate. Nothing else may mint a `RiskVerdict`.

Explicit non-bypass sources:

| Source | Why it cannot bypass |
|---|---|
| PM3-Strategy Engine | emits TradeIntent only; no import of PM4 internals that skip evaluate |
| PM3 forecasting / QRF | enrichment only; no ALLOW |
| CLI / operator command | may trigger evaluate; cannot force ALLOW |
| YAML / feature flag | flag off → `NullRiskGate` always DENY; flag on still deny-by-default |
| Env opt-in | test/research only; demo/live cannot open an execution path |
| Telegram / UI | not implemented; architecture desk is observe-only |
| Future operator “force approve” | must produce a **new** intent that still passes PM4 (ADR-007) |
| PM5 | not implemented; even if present, accepts only a referenced ALLOW verdict |

Deny-by-default:

1. Feature flag off → `NullRiskGate` (engine_unavailable).
2. Flag on, any required artifact missing / stale / inconsistent → DENY.
3. Flag on, all artifacts valid, a hard control fails → DENY / HALT / freeze.
4. Flag on, all controls pass → ALLOW or REDUCE, still not an order.
5. Ambiguous / unknown state → DENY (never a fake-healthy ALLOW).

## 5. Degraded modes

| Mode | New risk | Reduce / close (policy) | Telemetry / audit | Recovery |
|---|---|---|---|---|
| `normal` | allowed if admitted | allowed | live | n/a |
| `throttle` | sized down | allowed | live | automatic when heat/dd recover under policy |
| `protection` | reduced + extra vetoes | allowed | live | staged |
| `freeze` | blocked | allowed if risk-reducing-only policy | live | explicit |
| `close_only` | blocked | allowed | live | explicit |
| `no_new_risk` | blocked | blocked unless reducing | live | explicit |
| `kill_protected` | blocked | optional reducing path | live | **never silent; never auto-rearm** |
| `manual_review` | blocked | blocked | live | human reason required |
| `recovery` | throttled, staged | allowed | live | policy-gated |

Risk-reducing actions may later be allowed under restrictive modes. Risk-increasing
actions remain blocked whenever protection requires it.

## 6. Kill-switch scope model

`KillSwitchScope`:

- `symbol` — block one symbol
- `strategy` — block a sleeve / profile_id
- `cluster` — block a correlation cluster (e.g. USD block, European majors)
- `account` — block the whole book

`KillSwitchStatus`: `disarmed` | `armed` | `tripped` | `latched`

Behaviours when tripped/latched:

- block new risk
- block new orders (handoff ineligible)
- mark **cancel-working-orders intent** for future PM5 (placeholder only — no broker cancel)
- optionally allow risk-reducing path if `risk_reducing_only` policy is on
- record trigger, actor, scope, timestamp, correlation id
- recovery requires `recover(reason, actor)` plus cooldown / review policy
- **no hidden auto-rearm**

Automatic trip sources: drawdown `kill_protected`, control-integrity failure,
configured heat breach, operator latch.

## 7. Hierarchical risk budgeting

Not a flat per-trade percent. Allocation walks:

```text
account / book budget
  → strategy sleeve budget
    → regime budget
      → symbol budget
        → cluster budget
          → candidate budget
            → residual headroom
```

Each level consumes from the parent. A candidate is admitted only if **every**
level has residual headroom after the proposed risk. Drawdown and degraded mode
multiply the whole tree (throttle), they do not skip it.

## 8. Persistence expectations before PM7 / PM8

| State | Sequence 06 | Later owner |
|---|---|---|
| risk control state (heat, dd, kill) | in-memory repository | PM7 ledger + PM8 |
| incident log | in-memory | PM7 / PM8 |
| inventory / approvals | in-memory | PM8 |
| journal events | in-memory `NullStorage.append` | PM7 |
| durable cancel-on-disconnect | **not implemented** (placeholder policy) | PM5 + PM8 |
| broker positions | placeholder snapshot | PM5 + PM7 |

In-memory stores **must not pretend to be durable**. Restart loses control state.
That is an accepted Sequence 06 limitation, recorded in ADR-011.

## 9. Inventory / audit ownership

PM4 owns:

- algorithm inventory (this gate, version, owner)
- risk-control inventory (admission, sizing, heat, concentration, drawdown, pre-trade, kill)
- approval / last-review timestamps
- incident log (violations, bursts, trips)
- activation / re-enable reasons
- parameter / policy version history (in-memory)
- journal-friendly `EventType.RISK` / `HALT` / `ALERT` entries

Governance is not “a log line”. Every control change is a typed event.

## 10. No direct order creation

Forbidden in this package and in Sequence 06 wiring:

- `OrderRequest` construction
- `ExecutionProvider.submit`
- MT5 adapter calls
- Telegram send
- durable ledger writes
- paper-trading loops
- silent auto-rearm after kill

Allowed: recommended size as a number on `PositionSizingDecision`, plus a
`RiskVerdict`. Size is explanatory and binding for **future** PM5, not a send.

## 11. Feature flag / profile posture

- Catalog name: `enable_pm4_risk_gate`
- Field: `risk_engine`
- Safety: `requires-review`
- Default: **false** in every YAML
- Env opt-in: `BOTMODULEPROJECT1_FEATURE__ENABLE_PM4_RISK_GATE=true`
- Allowed profiles: **test** and **research** only
- Demo / live: must not create a real execution path
- Even when enabled, PM5 remains `DisabledExecution`

When the flag is false the composition root binds `NullRiskGate` (always DENY,
`is_ready() is False`). When true it binds `PM4RiskGateModule`.

## 12. Health / readiness honesty

- No fake-healthy ALLOW on insufficient evidence.
- Control-integrity, kill-switch, drawdown, and heat contributors are explicit.
- `is_ready()` means the **gate is assembled and can evaluate**, not that trading is authorized.
- Trading readiness remains: *the system is NOT ready for live, demo, paper, or production.*
- With the flag off, critical READINESS still fails closed via `NullRiskGate` (existing Sequence 01 behaviour).

## 13. Implementation sequence (after this plan)

1. Extend `contracts/v1/risk.py` backward-compatibly.
2. Create `botmoduleproject1/modules/pm4_risk_gate/` with the modular layout in the Sequence 06 prompt.
3. Keep `modules/pm4_risk/` as a compatibility re-export (no second implementation).
4. Wire container, settings, feature-flag copy, YAML example.
5. Tests + `pm4_risk_gate_test_traceability.md`.
6. ADR-011 (ADR-010 is already PM3 forecasting).
7. Sequence 06 report.

Build gate for this plan: **READY TO IMPLEMENT**.
