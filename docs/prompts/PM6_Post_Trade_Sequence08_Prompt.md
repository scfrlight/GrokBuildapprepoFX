# BOTMODULEPROJECT1 — SEQUENCE 08
# PM6 Post-Trade Controls, Real-Time Monitoring, Automated Surveillance,
# Incident Response, Audit Trail & Governance Intelligence

Source-of-truth for Sequence 08 (persisted from the authorizing prompt).

Project: BotModuleProject1.
Repository: GrokBuildapprepoFX.

IMPORTANT:
- No access to external master prompts Perplexity Spaces.
- This text is the source-of-truth for Sequence 08.
- Integration plan first: `docs/architecture/pm6_post_trade_integration_plan.md`.
- Do not connect Telegram UI, database migrations, or live trading.
- Do not declare the system ready to trade.

## 0. Current state (preserved)

PM1 kernel, PM2, PM3-Strategy Engine, PM3 forecasting/QRF, PM4 Risk Gate, PM5
Execution (OMS/EMS simulation/shadow) exist.

Safety posture:
- live disabled; no real MT5; no broker order send; no paper-trading loop
- no Telegram bot; no database schema/migrations; no durable event store
- `execution_permitted=false`; `DisabledExecution` default; recon without venue
  remains `degraded`
- system not ready for demo/paper/live/production

## 1. PM6 architectural role

PM6 is:

- continuous post-trade control layer
- real-time monitoring engine
- automated surveillance layer
- two-lines-of-defence monitoring layer
- incident detection/classification engine
- escalation/remediation orchestrator
- orderly withdrawal support layer
- audit evidence registry
- governance intelligence layer
- validation/review support layer
- operational truth publisher

PM6 is NOT a strategy engine, execution engine, risk-sizing engine, broker
adapter, replacement for PM4 or PM5, Telegram UI, generic dashboard, or
passive logging only.

Pipeline:

```text
PM2 context
→ PM3-Strategy Engine TradeIntent
→ PM3 ForecastOutput
→ PM4 RiskPublicationBundle
→ PM5 execution truth / simulation lifecycle / future broker truth
→ PM6 post-trade monitoring, surveillance, incidents, governance
```

## 2. Non-negotiable safety rules

1. PM6 must not create or send orders.
2. PM6 must not modify PM4 risk decisions.
3. PM6 must not modify PM5 broker state directly except through explicit
   control-plane protocol boundaries.
4. PM6 must not invent broker truth when PM5 has no venue.
5. `SIM-*` tickets must never be represented as MT5 broker tickets.
6. Reconciliation without external venue truth must remain `degraded` or
   `unavailable`, never silently `pass`.
7. PM6 must distinguish local OMS truth, simulation truth, broker truth,
   reconciled truth, unresolved mismatch, unknown, stale.
8. Stale, malformed, contradictory, or impossible event streams must be
   quarantined or rejected.
9. Critical incidents must not disappear without explicit closure, persistence
   handoff, or transfer.
10. No silent degradation of monitoring.
11. Any automatic protective action must be auditable.
12. Any orderly withdrawal recommendation must be explicit and traceable.
13. Recovery must be policy-driven and never silently re-enable trading.
14. PM6 must remain headless and UI-agnostic.
15. No database schema/migration is implemented in this Sequence.
16. In-memory state must be clearly labelled non-durable.
17. Feature flag must default to false in YAML.
18. Live profile remains hard-blocked.
19. No claim of demo, paper, live, or production readiness.
20. PM6 is an observability/control module, not an authority to bypass PM4 or PM5.

## 3. Core mission

Build PM6 as an institutional-grade post-trade governance and monitoring module
that continuously monitors activity, consumes PM5 execution truth and PM4
risk/control snapshots, operates post-trade controls, detects anomalies and
activity after freeze/kill/shutdown/withdrawal, separates operator vs
independent control lanes, classifies incidents, orchestrates
escalation/remediation, supports orderly withdrawal, preserves audit evidence,
publishes operational truth, and remains safe when venue truth is unavailable.

## 4. Build gate before implementation

Create `docs/architecture/pm6_post_trade_integration_plan.md` before coding.
Package: `botmoduleproject1/modules/pm6_post_trade/`.
Registry name: `pm6_monitoring` (Sequence 00 stub preserved).

Plan must show: PM5→PM6 execution flow; PM4→PM6 risk/control flow; simulation
versus broker truth; reconciliation handling; monitoring lanes; surveillance;
incident lifecycle; escalation/remediation; orderly withdrawal; PM7 handoff;
PM8/PM9 consumer boundary; no direct order creation; no direct risk or broker
mutation; in-memory limitation.

## 5. Institutional control principles

Continuous post-trade controls remain active while the system is active.
Recommendations through approved boundaries only: risk reduction, algorithm
restriction, strategy shutdown, symbol freeze, close-only, orderly withdrawal,
manual review.

Two lines of defence: operator/trader lane and independent risk/control lane.
They share events but keep separate summaries, priorities, escalation paths,
and decision semantics.

Incident response: detected, classified, triaged, escalated, contained,
remediated, reviewed, explicitly closed.

## 6–7. Inputs and validation

Consume typed PM5 execution publications, PM4 risk/control snapshots, optional
PM3 context, and operator actions.

Reject or quarantine: missing trace/source, unsupported version, stale or
future-dated timestamps, impossible ordering/lifecycle, contradictory
order/fill evidence, unresolved critical mismatch, invalid PM4 control state,
missing execution mode, `SIM-*` labelled as broker truth, duplicate evidence
without idempotency, missing causation for critical actions.

Outcomes: accepted / quarantined / rejected / degraded / requires_review.
Every quarantine/rejection needs reason code, human-readable reason, event id,
trace id, source, timestamp, audit record.

## 8. Data truth model

- `local_oms_truth`
- `simulation_truth`
- `broker_truth`
- `reconciled_truth`
- `unresolved_mismatch`
- `unknown`
- `stale`

Rules: `SIM-*` is simulation truth only; never reported as executed broker
activity. Reconciliation with no venue remains degraded/unavailable. Broker
truth, when later available, is separately represented. Contradictory truth
sources create an anomaly/incident path.

## 9. Required output contracts

`MonitoringSnapshot`, `SurveillanceAlert` / `PostTradeAlert`, `IncidentRecord`,
`EscalationAction`, `RemediationTask`, `OrderlyWithdrawalPlan`,
`AuditEvidenceBundle`, `GovernanceReviewPacket`, `ValidationReviewPacket`,
`OperationalTruthBundle`, `LaneSummary`, `ControlRequest`.

All outputs: typed, serializable, versioned, UTC-aware, immutable after
publication, traceable.

`ControlRequest.broker_command` cannot be true.
`OrderlyWithdrawalPlan` COMPLETED requires confirmation.
`AuditEvidenceBundle.durable=false`.
`OperationalTruthBundle` forbids `mt5_used`, `broker_side_effect`,
`BROKER_TRUTH`, `durable`.

## 10–13. State machines

Monitoring: healthy, watch, warning, degraded, critical, incident_active,
withdrawal_in_progress, review_pending, stabilized.

Incident: detected, triaged, classified, escalated, containment_in_progress,
remediation_in_progress, contained, resolved, review_pending, closed,
transferred_to_persistence.

Governance review: scheduled, in_review, evidence_compiled, decision_pending,
approved, remediation_required, closed.

Withdrawal: not_required, recommended, approval_pending, initiated,
in_progress, confirmed, completed, failed, manual_review.

Invalid transitions rejected. Incidents never disappear silently.

## 14–18. Engines

Post-trade controls detect: quantity drift, unexpected position, activity
after freeze/kill, unresolved mismatch, activity while control blocks it,
abnormal risk accumulation, unexpected repeated fills, activity after
withdrawal initiation, missing lifecycle, conflicting evidence, simulation
treated as broker truth.

Real-time monitoring: snapshots, freshness, stale-data, explicit degraded
mode, no fabricated broker values.

Surveillance detectors: bursts, repeated rejects/fills, duplicates,
cancel/modify storms, stale working orders, execution after freeze/kill,
exposure drift, mismatch, truth confusion, missing/impossible lifecycle,
abnormal latency, degraded recon, operator override anomalies, repeated
control breaches, incident recurrence, feed silence.

Alert fingerprint + idempotency; suppression retains evidence and keeps
duplicate count visible.

## 19–21. Incidents, escalation, withdrawal

Categories: technical, execution, reconciliation, risk/control, monitoring,
governance, operator, conduct, data-quality, security, recovery.

Types include: post_trade_control_breach, monitoring_alert_burst,
execution_anomaly, reconciliation_followup_required, kill_state_breach,
orderly_withdrawal_required, manual_override_incident, audit_evidence_gap,
validation_gap, unexpected_trading_continuation, stale_monitoring_data,
truth_provenance_conflict, repeated_execution_anomaly,
control_state_inconsistency.

Severity: info, low, medium, high, critical.

Escalation routes: immediate, same_session, same_day, scheduled_review.

Withdrawal is a plan/request to PM5 control plane (`broker_command=false`).
Cannot mark COMPLETED without confirmation. No auto-rearm.

## 22–24. Evidence, governance, validation

In-memory evidence labelled `non_durable_before_pm7`.

Governance packets for future PM8/PM9. No Telegram/UI imports.

Validation: insufficient data must be `unknown` / `insufficient_data` /
`not_available`. Do not claim precision/recall without labelled data.

## 25–27. Protocols, services, integration

Typed Protocols for engines, adapters, publication, health.
In-memory repositories isolated in infrastructure.

Register as `pm6_monitoring`. Dependencies: PM1, PM4, PM5.
PM6 cannot create an order, modify broker truth, or create risk approval.

## 28–29. Feature flags and config

Flags (YAML false; test/research env opt-in; demo cannot opt-in):

- `enable_pm6_post_trade` — master bind
- `enable_pm6_surveillance`
- `enable_pm6_incident_response`
- `enable_pm6_governance_intelligence`
- `enable_pm6_withdrawal_planner`

No flag enables MT5, order sending, or bypass of PM4/PM5.
Config: `configs/pm6_post_trade.example.yaml`. No Telegram, no DB credentials,
no direct broker command configuration.

Default bind when flags off: `NullMonitoring`.

## 30–33. Structure, tests, docs, prohibitions

Package layout under `botmoduleproject1/modules/pm6_post_trade/`.
Tests covering intake, truth, controls, lanes, surveillance, alerts,
incidents, withdrawal, governance, integration, safety.

Docs: this prompt, integration plan, test traceability, sequence_08_report,
ADR-013, README.

Do not: create/submit orders, call MT5, modify broker positions, bypass PM5
control plane, change PM4 sizing/admission, fabricate broker truth, call
`SIM-*` broker tickets, build Telegram UI, add database migrations, silently
suppress incidents, auto-rearm after kill, replace PM5 recon, replace PM4
risk gate, claim live/demo/paper readiness.

## 34. Final report / next step

Trading readiness (exact substance):

The system is NOT ready for live trading, demo trading, paper trading, or production.

Exact next step: Sequence 09 — PM7 Persistence, Event Ledger, Reconciliation
Store & Durable Audit Layer.
