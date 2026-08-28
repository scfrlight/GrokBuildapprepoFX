# PM6 Post-Trade — Integration Plan (Sequence 08)

Status: **Accepted before implementation**  
Date (UTC): 2026-08-28  
Package: `botmoduleproject1/modules/pm6_post_trade/`  
Registry name: `pm6_monitoring` (Sequence 00 stub name, preserved)  
Feature flags (YAML false; test/research env opt-in):
- `enable_pm6_post_trade` (`feature_flags.pm6_post_trade`) — master bind
- `enable_pm6_surveillance` (`feature_flags.pm6_surveillance`)
- `enable_pm6_incident_response` (`feature_flags.pm6_incident_response`)
- `enable_pm6_governance_intelligence` (`feature_flags.pm6_governance`)
- `enable_pm6_withdrawal_planner` (`feature_flags.pm6_withdrawal`)

This plan is the pre-implementation gate required by Sequence 08. PM6 is the
**continuous post-trade control / surveillance / incident / governance** layer.
It is not a strategy engine, not a risk sizer, not an OMS/EMS, and not a broker.

---

## 1. Position in the pipeline

```text
PM2 RankedCandidate
  → PM3-Strategy Engine TradeIntent
    → PM3 forecasting / QRF ForecastOutput
      → PM4 RiskPublicationBundle
        → PM5 ExecutionPublicationBundle   (simulation / shadow; no venue)
          → PM6 Post-Trade Controls          (this module)
            → OperationalTruthBundle
              → future PM7 persistence
                → future PM8/PM9 consumers
```

Hard cuts:

- PM4 remains the only risk authorizer. PM6 never issues ALLOW or sizes risk.
- PM5 remains the only execution authority. PM6 never submits, cancels at a
  venue, or mutates OMS state except by **typed control requests**.
- `SIM-*` is simulation truth only. Never labelled an MT5 ticket.
- Reconciliation without a venue stays `degraded` / `unavailable`. Never silent pass.
- Default bind remains `NullMonitoring` when the master flag is off.

## 2. Event flow

| Source | Object | PM6 use |
|---|---|---|
| PM5 | `ExecutionPublicationBundle` | lifecycle, fills, tickets, recon, control, quality, mode |
| PM5 | `OrderRecord` / `FillEvent` / `ControlActionRecord` | post-trade controls, surveillance |
| PM5 | `ReconciliationRecord` | truth class; degraded vs mismatch vs critical |
| PM4 | `RiskPublicationBundle` | kill, freeze, admission, sizing cap, heat |
| Operator | typed action + actor + reason | audit, override anomalies |
| Journal | `JournalEntry` (optional) | compatibility ingest; not a second truth |

PM6 does **not** consume PM2/PM3 as a submit path. Optional context only.

## 3. Simulation versus broker truth

| Class | When | May report as executed broker activity? |
|---|---|---|
| `local_oms_truth` | OMS record present | no |
| `simulation_truth` | mode=simulation or ticket `SIM-*` | **no** |
| `broker_truth` | venue available (Sequence 08: never) | n/a |
| `reconciled_truth` | recon `pass` with broker_truth_available | Sequence 08: never |
| `unresolved_mismatch` | recon mismatch/critical | no |
| `unknown` / `stale` | missing / expired feed | no |

Rules:

1. PM5 `SIM-*` → `simulation_truth`.
2. No venue → recon remains `degraded`; monitoring state at least `degraded`.
3. Labelling `SIM-*` as broker truth → intake reject / `truth_provenance_conflict`.
4. PM6 never fabricates broker fills, tickets, or positions.

## 4. Two monitoring lanes

| Lane | Audience | Focus |
|---|---|---|
| Operator | desk / future PM9 | working orders, fills, mode, open incidents, required response |
| Independent control | risk/governance | kill breaches, freeze violations, recon, provenance, drift |

Lanes share events. They keep **separate** summaries, priorities, and
recommended actions. Neither overwrites the other.

## 5. Incident lifecycle

`detected → triaged → classified → escalated → containment_in_progress →
contained / remediation_in_progress → resolved → review_pending → closed`

Alternate exit: `transferred_to_persistence` (PM7 handoff, still non-durable here).

Illegal transitions raise. Incidents cannot vanish: close, transfer, or
explicit suppression **with reason and retained evidence**.

## 6. Orderly withdrawal boundary

PM6 may **recommend** and **plan**:

- freeze new / close-only / no-new-risk
- cancel working (request to PM5 control plane)
- symbol / strategy / cluster / account scope

PM6 must **not**:

- send a broker command
- call MT5
- mark withdrawal `completed` without confirmation
- auto-rearm a kill-switch

## 7. PM7 / PM8 / PM9 handoff

`OperationalTruthBundle` + `AuditEvidenceBundle` are the downstream payloads.
`durable=false`, `persistence_handoff=non_durable_before_pm7`.
No Telegram, no DB schema, no migrations in Sequence 08.

## 8. Default bind

| Flag state | Bind |
|---|---|
| all false (YAML) | `NullMonitoring` |
| `enable_pm6_post_trade` | `PM6PostTradeModule` |
| sub-flags off | engines present but skip optional packets / auto-withdrawal |

No flag opens MT5, orders, or live.

## 9. Implementation order

1. This plan (gate).
2. `contracts/v1/post_trade.py` + journal/alert extensions.
3. Package `modules/pm6_post_trade/`.
4. Feature flags + settings + container.
5. Tests + traceability.
6. Docs / ADR-013 / README.
7. Architecture desk (observe-only).

Do not claim demo / paper / live / production readiness.
