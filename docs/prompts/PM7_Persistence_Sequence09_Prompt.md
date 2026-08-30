# BOTMODULEPROJECT1 — SEQUENCE 09
# PM7 Persistence, Event Ledger, Reconciliation Store & Durable Audit Layer
# Persistent Trade Ledger, Evidence Store, Replay Engine,
# Reporting Warehouse, Integrity Verification, Retention & Audit Analytics

Source-of-truth for Sequence 09 (persisted from the authorizing prompt).

Project: BotModuleProject1.
Repository: GrokBuildapprepoFX.

IMPORTANT:
- No access to external master prompts.
- This text is the source-of-truth for Sequence 09.
- Integration plan first: `docs/architecture/pm7_persistence_integration_plan.md`.
- Do not declare the system ready to trade because a journal exists.
- Do not connect a real broker path. Do not mutate committed history.

## 0. Current state

PM1 kernel, PM2, PM3-Strategy Engine, PM3 forecasting/QRF, PM4 Risk Gate,
PM5 Execution, PM6 Post-Trade exist.
Safety stubs: NullRiskGate DENY, DisabledExecution raises, NullMonitoring default,
live disabled, no real MT5, no paper loop, no Telegram, in-memory PM4–PM6.
`execution_permitted=false` remains. SIM-* is simulation truth.
Reconciliation without a venue stays degraded.

## 1. PM7 role

PM7 is persistent institutional memory: append-only journal, evidence store,
reconciliation history, deterministic replay, snapshots, reporting warehouse,
audit analytics, integrity/tamper detection, retention/archival, query,
export, publication gateway.

PM7 is NOT a strategy engine, forecasting engine, risk engine, OMS/EMS,
broker adapter, post-trade monitoring engine, Telegram/UI, or generic DB wrapper.

## 2. Non-negotiable safety rules

Never create/send broker orders. Never modify PM4 decisions or PM5 broker truth.
Never replace PM6 incident logic. Historical journal entries are append-only
after commit. Corrections are governed new events. Preserve source, lineage,
timestamps, provenance. SIM-* remains simulation. Recon without venue stays
degraded/unavailable. No destructive purge outside policy. Legal freeze blocks
purge. Integrity mismatch is visible. Recovery must not silently rewrite
history. Downstream consumers do not write the canonical stream. No secrets.
No live trading. No claim of trading readiness.

## 3. Core mission

Capture PM2–PM6 events, persist them, preserve order and causal lineage, store
recon history, build evidence, snapshot, replay, detect divergence, verify
integrity, apply retention, query, report, export, support PM8/PM9, stay safe
if downstream is offline, distinguish simulation from future broker truth.

## 4. Build gate

Inspect repository. Package `botmoduleproject1/modules/pm7_persistence/`.
Registry name `pm7_ledger`. Create the integration plan BEFORE implementation.

## 5. Persistence modes

disabled | memory | file_backed | sqlite_local | durable_candidate |
production_durable (future-controlled, refused).
Default: NullLedger when flag off; memory when flag on.
No cloud credentials. No ambient DATABASE_URL. Local sqlite is not production
distributed durability.

## 6–20. Functional domains

Event ingestion gateway; truth provenance; canonical journal; reconciliation
store; evidence store; replay engine; snapshot manager; integrity/tamper
detection (SHA-256, hash chain, detection not proof); retention/archival
(hot/warm/cold, freeze, no silent delete); query/retrieval (authorized);
reporting warehouse (insufficient_data honest); audit analytics; export
packaging (JSON+markdown+checksum, no secrets); recovery/backup metadata only.

## 21–22. Integration

PM1 registry, manifest, capabilities, health.
Consume PM4 RiskPublicationBundle, PM5 ExecutionPublicationBundle,
PM6 OperationalTruthBundle. Do not reimplement those modules.

## 23. Feature flags

enable_pm7_persistence (master bind), enable_pm7_journal, enable_pm7_replay,
enable_pm7_integrity, enable_pm7_retention, enable_pm7_reporting.
YAML false. Test/research env opt-in. Demo cannot opt-in. Live hard-blocked.
Prefixed env only: BOTMODULEPROJECT1_FEATURE__ENABLE_PM7_*.

## 24. Configuration

configs/pm7_persistence.example.yaml. Fail fast. No production_durable.
No MT5. No auto-rearm. No destructive purge by default. simulate_archive true.

## 25–27. Folder structure, Protocols, application services

As specified in the Sequence 09 prompt. Headless queries only. No Telegram.

## 28. Testing

Journal, provenance, recon, evidence, replay, snapshots, integrity, retention,
query/export, reports, recovery, integration, safety. Traceability matrix.

## 29. Documentation

This prompt, integration plan, traceability, sequence_09_report, README, ADR-014.

## 30. Prohibitions

No broker orders, MT5, PM4/PM5/PM6 mutation, silent purge, secrets,
tamper-proof claims, production-durable claims for sqlite/file, fabricating
broker truth, presenting SIM-* as broker tickets, Telegram, live trading,
silent corruption repair.

## 31. Trading readiness

The system is NOT ready for live trading, demo trading, paper trading, or production.

Exact next step (historical): Sequence 10 — PM8 Operator Control Plane.
Canonical correction 2026-08-30: next after this PM7 work is Sequence 09
PM8 Database Consolidation. Operator is Sequence 13. See `docs/SEQUENCE_CORRECTION.md`.
