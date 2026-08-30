# Architecture inventory — reconciliation 2026-08-30

Status: **reconciliation**, not Sequence 15.  
HEAD at generation: `9402421bce53fa1c81a8dd4e2dfc770acdb5d988` (see `docs/evidence/reconciliation/`).
  
Sequence 15+ remains **BLOCKED**.

Sources of truth (priority): (1) live safety constraints in this repo; (2) persisted PM sequence prompts; (3) reconstructed `PM8a_Build_Spec.md`; (4) `SEQUENCE_CORRECTION.md`; (5) `MODULE_NUMBERING_MAP.md`; (6) README/docs; (7) tests as behaviour evidence, not as a substitute for spec.

## 1. Source files

| Artifact | Path | Status |
|---|---|---|
| Master Orchestration Prompt | `Grok_Build_Master_Orchestration_Prompt.md` | **SOURCE-MISSING** |
| PM1 Master | `docs/prompts/PM1_Master_Prompt.md` | present |
| Seq 02 config | `docs/prompts/PM1_Sequence02_Configuration_Governance_Prompt.md` | present |
| PM2 / Seq 03 | `docs/prompts/PM1_Sequence03_PM2_MarketContext_Prompt.md` | present |
| PM3-SE Seq 04 | `docs/prompts/PM3_Strategy_Engine_Sequence04_Prompt.md` | present |
| PM3-FX Seq 05 | `docs/prompts/PM3_Forecasting_Sequence05_Prompt.md` | present |
| PM4 Seq 06 | `docs/prompts/PM4_Risk_Gate_Sequence06_Prompt.md` | present |
| PM5 Seq 07 | `docs/prompts/PM5_Execution_Sequence07_Prompt.md` | present |
| PM6 Seq 08 (SoT for PM6) | `docs/prompts/PM6_Post_Trade_Sequence08_Prompt.md` | present (`PM6_Master_Prompt.md` filename **SOURCE-MISSING**; this file is the authorized SoT) |
| PM7 Seq 09 prompt (SoT for PM7) | `docs/prompts/PM7_Persistence_Sequence09_Prompt.md` | present (`PM7_Master_Prompt.md` filename **SOURCE-MISSING**) |
| PM8 operator (historical Seq 10 → canonical 13) | `docs/prompts/PM8_Operator_Sequence10_Prompt.md` | present (mislabeled filename) |
| Original PM8a Drive spec | original `PM8a_Build_Spec.md` | **SOURCE-MISSING** |
| Reconstructed PM8a | `docs/prompts/PM8a_Build_Spec.md` | present, reconstructed 2026-08-30 |
| PM9a studio master | `PM9a_Strategy_Fine_Tune_Studio_Master_Prompt.md` | **SOURCE-MISSING** |
| Sequence correction | `docs/SEQUENCE_CORRECTION.md` | present |
| Numbering map | `docs/MODULE_NUMBERING_MAP.md` | present |
| Seq 14 traceability | `docs/TRACEABILITY_MATRIX.md` | present (Seq 14 + this reconciliation) |
| ADRs 001–016 | `docs/adr/` | present |
| PM8/PM8a gap matrix | `docs/PM8_PM8A_GAP_MATRIX.md` | this reconciliation |
| Known limitations | `docs/known_limitations.md` | this reconciliation |

## 2. Sequence delivery vs capability vs master

“Sequence delivered” means the authorized sequence shipped code + tests + a report. It is **not** the same as “full PM Master capability” or “trade-ready”.

| Seq | Canonical name | Package | Sequence delivery | Capability vs master / spec | Trading-capable | Persistence-authoritative | Default bind | Flag |
|---|---|---|---|---|---|---|---|---|
| 00 | reconnaissance | `docs/` | COMPLETE | N/A | no | no | — | — |
| 01 | PM1 kernel | `botmoduleproject1.app` | COMPLETE | COMPLETE for kernel | no | no | always | — |
| 02 | configuration | `app/settings.py` | COMPLETE | COMPLETE for Seq 02 | no | no | always | — |
| 03 | PM2 market context | `modules/pm2_market_context` | COMPLETE | COMPLETE for Seq 03 scope; HMM/GMM stubs off | no | no | `NullMarketData` | `enable_pm2_market_data` |
| 04 | PM3 strategy engine | `modules/pm3_strategy_engine` | COMPLETE | COMPLETE for TradeIntent-only Seq 04 | no (intents ≠ orders) | no | `NullSignals` | `enable_pm3_strategy_engine` |
| 05 | PM3 forecasting | `modules/pm3_forecasting` | COMPLETE | PARTIAL vs fitted QRF (**NOT-IN-SCOPE** / blocked) | no | no | `NullModel` | `enable_forecasting` |
| 06 | PM4 risk gate | `modules/pm4_risk_gate` | COMPLETE | COMPLETE as exclusive deny-by-default gate (flag off) | no | no | `NullRiskGate` DENY | `enable_pm4_risk_gate` |
| 07 | PM5 OMS/EMS sim | `modules/pm5_execution` | COMPLETE | COMPLETE for simulation; broker adapter **BLOCKED** | no (SIM-* not broker) | no | `DisabledExecution` | `enable_pm5_simulation` |
| 08 | PM6 post-trade | `modules/pm6_post_trade` | COMPLETE | COMPLETE for in-memory Seq 08; not Seq 14 | no | no | `NullMonitoring` | `enable_pm6_post_trade` |
| 09 | PM8 DB consolidation | `modules/pm8_persistence` | COMPLETE | **PARTIAL vs PG**; SQLite named projections / isolated restore-apply present | no | **yes** (canonical downstream API when flag on) | `NullStorage` | `enable_pm8_persistence` |
| 10 | PM8a hardening | same package | COMPLETE | **PARTIAL** (verify exists; restore-apply **ABSENT**) | no | yes (same API) | off | same |
| 11 | MT5 demo engine | `modules/mt5_execution_engine` | COMPLETE (sim/test-safe) | Demo simulation; real terminal **BLOCKED** | no (`DEMO-*` not broker truth) | no | fail-closed / unused unless flags | `enable_mt5_demo_adapter` |
| 12 | unified runtime | `botmoduleproject1/runtime` | COMPLETE | COMPLETE for observe pipeline; no live path | no | uses PM8 API if injected | off | `enable_unified_runtime` |
| 13 | operator UX | `modules/pm8_operator` | COMPLETE | Telegram Bot API **BLOCKED** | no | binds PM8 API observe-only | `NullOperator` | `enable_pm8_operator` |
| 14 | observability | `modules/observability` | COMPLETE (observe-only) | COMPLETE for Seq 14 diagnostics; **not PM6** | no; `trading_readiness` forced false | no | always-on | none |
| 15+ | — | — | **BLOCKED** | — | — | — | — | none |

## 3. PM identity (must not collapse)

| Identity | Is | Is not |
|---|---|---|
| **PM6** | `pm6_post_trade` — post-trade monitoring, surveillance, incidents, withdrawal **plans**, governance. Registry name `pm6_monitoring`. | Not MT5 execution. Not Seq 14 observability. Not a risk sizer. Not a broker adapter. |
| **PM7** | `pm7_persistence` (registry `pm7_ledger`) — **PARTIAL / evidence-journal subset**. In-memory (optional file/sqlite write-append) append-only journal, corrections, hash-chain detection, replay/snapshot/retention/query/export at Sequence 09 depth. | Not production durable. Not the canonical downstream data API. Not a broker adapter. Canonical Seq 09 is PM8, not this package. |
| **PM8** | `pm8_persistence` — `PersistenceApiV1` CQRS facade, families, idempotency edges, sqlite schema. | Not the operator plane. Not a venue. |
| **PM8a** | Build-spec + Seq 10 hardening of **the same** `pm8_persistence` package (migrations, backup verify, restart drill). | Not a separate business module. Original Drive spec **SOURCE-MISSING**. |
| **Seq 13 operator** | `pm8_operator` (alias `pm9_operator_ux`) | Not PM8 persistence. Not Telegram Bot API. |
| **Seq 14 observability** | `modules/observability` — logs, metrics, health/readiness planes, taxonomy, runbooks. | Not PM6. Must not set `trading_readiness=true`. |

## 4. Feature flags

All catalog flags default **false**. Dangerous flags are env-only. `enable_live_trading` / `enable_live_execution` always raise. `enable_telegram_control` refused. `enable_pm5_broker_adapter` / `enable_mt5_demo_execution` refused in Seq 07. No Sequence 15 flag exists.

| Field | Catalog name | Default bind when false | Safety |
|---|---|---|---|
| `market_data` | `enable_pm2_market_data` | `NullMarketData` | requires-review |
| `strategy_engine` | `enable_pm3_strategy_engine` | `NullSignals` | requires-review |
| `forecasting` | `enable_forecasting` | `NullModel` | requires-review |
| `risk_engine` | `enable_pm4_risk_gate` | `NullRiskGate` DENY | requires-review |
| `pm5_simulation` | `enable_pm5_simulation` | `DisabledExecution` | requires-review |
| `execution` | `enable_pm5_execution` | refused / unused | dangerous |
| `pm5_broker_adapter` | `enable_pm5_broker_adapter` | refused | dangerous |
| `mt5_demo_execution` | `enable_mt5_demo_execution` | refused Seq 07 | dangerous |
| `live_execution` | `enable_live_execution` | always fail-closed | dangerous |
| `telegram` | `enable_telegram_control` | refused | dangerous |
| `fine_tune_studio` | `enable_fine_tune_studio` | studio off | requires-review |
| `live_trading` | `enable_live_trading` | always fail-closed | dangerous |
| `pm6_post_trade` (+ surveillance/incident/governance/withdrawal) | `enable_pm6_*` | `NullMonitoring` | requires-review |
| `pm7_persistence` (+ journal/replay/integrity/retention/reporting) | `enable_pm7_*` | `NullLedger` | requires-review |
| `pm8_operator` (+ hitl/command_audit) | `enable_pm8_operator` | `NullOperator` | requires-review |
| `pm8_persistence` (+ outbox/projections) | `enable_pm8_persistence` | `NullStorage` | requires-review |
| `mt5_demo_adapter` / `exit_engine` | Seq 11 | unused unless env | requires-review |
| `unified_runtime` | `enable_unified_runtime` | unused | requires-review |

YAML files under `configs/*.example.yaml` keep these false. Unprefixed ambient env is ignored.

## 5. Composition / adapters / contracts / CI

- Composition: `botmoduleproject1/app/container.py`. Registry names: `platform`, `pm2_market_context`, `pm3_strategy_engine`, `pm3_forecasting`, `pm4_risk`, `pm5_execution`, `pm7_ledger`, `pm8_persistence`, `notifications`, `pm6_monitoring`, `pm8_operator`, `observability`.
- Persistence adapters: PM7 backends under `pm7_persistence/infrastructure` (memory / file write-append / sqlite write-append); PM8 `SqliteStore`; defaults `NullLedger` / `NullStorage`.
- Execution adapters: `DisabledExecution`; PM5 simulation (`SIM-*`); Seq 11 `DemoMt5Gateway` (`simulated=True` in tests); Seq 07 `Mt5BrokerAdapter.submit` raises. Adapter package: `botmoduleproject1/adapters/mt5`.
- Observability: always-on `ObservabilityModule`; structlog JSON. Kernel health aggregator remains; Seq 14 planes are independent.
- Telegram: `botmoduleproject1/adapters/telegram/transport.py` — `RealTelegramTransport()` raises.
- Public contracts: `botmoduleproject1/contracts/v1/{alerts,execution,forecasting,identity,journal,market,observability,operator,persistence,pm2,pm8_persistence,post_trade,risk,roles,session,signals,strategy,strategy_engine,time,tuning}.py`.
- CI: `.github/workflows/tests.yml` (pytest 3.11/3.12 with captured exit; doctor-py310 fail-fast; seq14 hygiene). Piped `pytest | tee` / `| grep` **banned**.
- Tests: `tests/unit`, `tests/contract`. Reconciliation invariants: `tests/unit/test_reconciliation_boundaries.py`.
- Evidence: `docs/evidence/` (seq14, ci runs, doctor, restart drill) and `docs/evidence/reconciliation/`.

## 6. PM6 boundary (4A)

SoT: `docs/prompts/PM6_Post_Trade_Sequence08_Prompt.md`. Filename `PM6_Master_Prompt.md` is **SOURCE-MISSING**.

| Check | Result |
|---|---|
| Package is post-trade/governance | yes — `modules/pm6_post_trade` (monitoring, surveillance, incidents, withdrawal **plans**, governance, evidence) |
| Contains MT5 order submission | **no** (AST + runtime tests) |
| Performs risk sizing | **no** (no PM4 sizing import, no sizer) |
| Substitutes PM4 | **no** |
| Substitutes PM5 execution/reconciliation | **no** (observes publications) |
| State mixed with persistence | **no** (in-memory; PM7/PM8 consume publications) |
| Seq 14 declared as PM6 | **no** — `ObservabilityModule` registry `observability`; README “Not PM6” |
| Default bind | `NullMonitoring` |

Identity split: **PM6 = business/control/governance monitoring**; **Sequence 14 = cross-cutting diagnostics/operations**. They must not be collapsed.

## 7. PM7 capability matrix (4B)

SoT: `docs/prompts/PM7_Persistence_Sequence09_Prompt.md`. Filename `PM7_Master_Prompt.md` is **SOURCE-MISSING** — do not invent missing Master clauses.

Module-level classification: **`PM7 PARTIAL / evidence-journal subset`**.

| Capability | Status | Implementation | Test | Limitation |
|---|---|---|---|---|
| append-only journal | PARTIAL | `pm7_persistence/journal` | `test_pm7_journal.py` | in-memory; file/sqlite write-append **do not reload** |
| immutable committed rows | COMPLETE (in-process) | `mutate()` raises `ImmutableJournalError` | `test_immutable_committed_event` | process lifetime |
| event ordering | COMPLETE (in-process) | sequence + hash chain | `test_ordering` | process lifetime |
| evidence bundles | COMPLETE (in-process) | `evidence/` | `test_pm7_evidence.py` | process lifetime |
| replay | COMPLETE (in-process) | `replay/` | `test_pm7_replay.py` | does not mutate source; not PM8 replay |
| snapshot handling | COMPLETE (in-process) | `snapshot/` | `test_pm7_snapshots.py` | process lifetime |
| integrity verification | PARTIAL | hash-chain detection, not proof | `test_pm7_integrity.py` | claim `tamper_detection_only` |
| lineage | COMPLETE (in-process) | `causation_id` / `lineage_refs` | `test_causal_lineage` | — |
| retention policy | PARTIAL | hot/warm/cold + freeze | `test_pm7_retention.py` | `simulate_archive`; in-memory |
| archive manifest | COMPLETE (in-process) | retention archive | `test_archive_manifest` | not durable bytes |
| query/retrieval | COMPLETE (in-process) | authorized query | `test_pm7_query.py` | — |
| export packaging | COMPLETE (in-process) | JSON+md+checksum | `test_export_manifest_checksum_no_secrets` | — |
| reporting datasets | PARTIAL | in-memory warehouse | `test_pm7_reports.py` | not a reporting warehouse |
| audit analytics | PARTIAL | lineage-aware reports | `test_pm7_reports.py` | not warehouse analytics |
| backup separation | PARTIAL | metadata only | `test_pm7_recovery.py` | byte backup is PM8a |
| corruption detection | COMPLETE (in-process) | chain mismatch → COMPROMISED | `test_mismatch_compromised` | — |
| repair by correction event | COMPLETE (in-process) | `correct()` new event | `test_correction_instead_of_mutation` | never rewrite |
| production durable warehouse | **ABSENT / BLOCKED** | `production_durable` refused | `test_production_durable_refused` | — |
| canonical downstream API | **NOT-IN-SCOPE** (PM8) | consumers must use `PersistenceApiV1` | numbering map | PM7 stays a journal subset |

Default bind: `NullLedger`. Flag YAML false. Demo cannot opt-in. Not a broker adapter.

## 8. Safety locks (must remain)

YAML flags false · `trading_readiness=false` · `accept_trade=false` · MT5 venue UNAVAILABLE when flags off · `python -m botmoduleproject1 live` fail-closed · Telegram unbound · PM4 exclusive risk gate · `SIM-*`/`DEMO-*` not broker truth.

Boundary rules verified by `tests/unit/test_reconciliation_boundaries.py`:

1. PM4 exclusive risk gate.
2. PM5 = Seq 07 simulation OMS/EMS.
3. Seq 11 = `mt5_execution_engine`, Demo-only simulation-safe.
4. PM6 = post-trade monitoring/governance.
5. PM7 = persistent journal/evidence/replay subset.
6. PM8 = canonical downstream persistence API.
7. PM8a = build-spec/hardening of PM8, not a second module.
8. Seq 13 = operator UX/control plane.
9. Seq 14 = cross-cutting observability.
10. Operator/observability cannot submit orders.
11. PM7/PM8 cannot silently mutate committed history.
12. PM6 cannot perform PM4 sizing.
13. PM7/PM8 cannot become broker adapters.
14. Seq 14 cannot set trading readiness true.

The system is NOT ready for live trading, demo trading, paper trading, or production.
