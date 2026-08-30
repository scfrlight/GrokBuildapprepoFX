# Sequence Correction — return to Master Orchestration order

Date (UTC): 2026-08-30  
Author: implementation-orchestrator  
Status: **Accepted** — architect correction prompt 2026-08-30  
Git home: `scfrlight/GrokBuildapprepoFX`  
Kernel SHA: **`8fd45f624bc088ec7ebe47151333605397c06b15`** (main, 2026-08-30; parent `a2a1890`)

## 1. Missing original specs (escalation record)

Searched GitHub (`scfrlight/*`) and Google Drive before any new sequence work.

| File | Found |
|---|---|
| `Grok_Build_Master_Orchestration_Prompt.md` | **No** |
| `PM8a_Build_Spec.md` | **No** |
| `PM9a_Strategy_Fine_Tune_Studio_Master_Prompt.md` | **No** |

**Decision:** do **not** block. The architect's 2026-08-30 correction prompt is the authorized source of truth for sequence **order** and for PM8/PM8a/PM6-MT5/runtime/operator scope. A reconstructed `docs/prompts/PM8a_Build_Spec.md` is persisted from that prompt (sections 13 / 15 / 16 / 19 / 20) plus existing PM7 contracts. If the original Drive files appear later, reconcile before Sequence 14.

No live / demo / paper / production trading path is opened by this correction.

## 2. What was wrong

Built **Sequence 10** implemented **PM8 Operator Control Plane** (RBAC, HITL, simulated Telegram transport). That content belongs to **canonical Sequence 13** (PM9 Operator UX & Telegram Control Plane).

That skip left:

| Canonical sequence | Required content | State before correction |
|---|---|---|
| **09** | PM8 Database Consolidation & Data Integrity | **Skipped.** `pm8_persistence` was `NullStorage`. PM7 journal (historical Sequence 09 report) is a different module. |
| **10** | PM8a Migration, Backup & Recovery Hardening | **Skipped.** |
| **11** | PM6 MT5 Execution & Exit Engine (Demo-only) | **Skipped.** PM5 is simulation-only; MT5 adapter is a placeholder; `submit()` raises. |
| **12** | Unified Runtime Orchestrator | **Skipped.** `runtime/` is a heartbeat host, not a pipeline. |
| **13** | PM9 Operator UX & Telegram Control | Built early, **mislabeled Sequence 10**. |

Operator console over an unconsolidated store and a non-existent venue engine is an unsafe order. Code is kept, not deleted.

## 3. Reclassification (Step 1)

| Artifact | Action |
|---|---|
| `modules/pm8_operator` | **FROZEN.** Relabeled Sequence 13 preview / early build. Feature flags cannot bind it. |
| `modules/pm9_operator_ux` | Still a re-export. Frozen with the operator plane. |
| Historical `docs/architecture/sequence_10_report.md` | Banner: mislabeled; canonical Sequence 13. Not deleted. |
| Historical `docs/architecture/sequence_09_report.md` | Remains the **PM7 journal** report. Canonical Sequence 09 is now PM8 consolidation (new report). |
| `OPERATOR_PLANE_FROZEN` | Lifted to `False` in `botmoduleproject1/app/sequence_gate.py` after Sequences 09–12 build gates in this correction wave. Freeze remains testable via monkeypatch. |

Do not enable `enable_pm8_operator` / `enable_pm8_hitl` / `enable_pm8_command_audit` until Sequences 09–12 pass their build gates.

## 4. Canonical sequence map (00–13)

| Seq | Canonical name | Package / home | Status after this correction wave |
|---|---|---|---|
| 00 | Repository reconnaissance | docs + skeleton | Done (historical) |
| 01 | PM1 platform kernel | `app/` | Done |
| 02 | Configuration governance | settings/flags | Done |
| 03 | PM2 market context | `pm2_market_context` | Done (flag off) |
| 04 | PM3-Strategy Engine | `pm3_strategy_engine` | Done (flag off) |
| 05 | PM3 forecasting / QRF | `pm3_forecasting` | Done (flag off) |
| 06 | PM4 Risk Gate | `pm4_risk_gate` | Done (flag off) |
| 07 | PM5 OMS/EMS simulation | `pm5_execution` | Done (flag off; SIM-*) |
| 08 | PM6 post-trade controls | `pm6_post_trade` | Done (flag off) |
| **09** | **PM8 database consolidation** | `pm8_persistence` | **Done this wave — 12/12 gate tests** |
| **10** | **PM8a migration / backup / recovery** | `pm8_persistence` + runbooks | **Done this wave — 5/5 gate tests; restart drill logged** |
| **11** | **MT5 Demo execution & exit** (Master Orchestration *title* only) | **`mt5_execution_engine`** + `adapters/mt5` | **Done — package is not pm6; `pm6_post_trade` untouched** |
| **12** | **Unified runtime orchestrator** | `botmoduleproject1/runtime/` | **Done this wave — 2/2 gate tests** |
| **13** | **Operator UX / Telegram control** | `pm8_operator` (reuse, unfreeze) | **Done this wave — reuse + bind; 4/4 correction tests** |

Full suite after the wave: see `docs/evidence/pytest-3.11.log` and GitHub Actions (Python 3.11+). ADR-008 floor is 3.11+.

### Dual PM6 naming — resolved

Master Orchestration **titles** Sequence 11 “PM6 MT5 Execution & Exit Engine”. That title is not a package name. The package is **`mt5_execution_engine`**. **`pm6_post_trade` is the only PM6 package.** Map: `docs/MODULE_NUMBERING_MAP.md`.

### Dual Sequence 09 naming — previous-session error

Calling Sequence 09 “PM7 journal” was an error of a previous session. PM7 journal **content stays** in `pm7_persistence` (PM1–PM7 range). Canonical Sequence 09 is PM8 consolidation (`pm8_persistence`). Details: `docs/MODULE_NUMBERING_MAP.md` §3.

## 5. Return plan (strict order)

1. **Step 1 (this file)** — reclassify + freeze operator.
2. **Sequence 09** — schema families, 19 repository protocols, 20 services, versioned API, integrity/repair, backup/export, four idempotency edges, outbox/inbox.
3. **Sequence 10** — versioned migrations + rollback, backup schedules, restore verification, drift tests, restart drills, runbooks.
4. **Sequence 11** — Demo-only MT5 adapter, capability checks, idempotent routing, duplicate guards, bounded retries, reconciliation (never silent pass), structural SL/TP, breakeven, time stops, exit lifecycle. `live` stays fail-closed.
5. **Sequence 12** — single pipeline with graceful shutdown, reconnect, health, stale-data stop, recovery-before-trading.
6. **Sequence 13** — unfreeze existing operator module; bind it to Sequence 09 API and Sequence 11 engine. Do not rewrite from scratch.

Sequence 14+ requires an explicit architect review after the post-correction audit.

## 6. Hard bans (unchanged)

- No skip of 09/10/11.
- No live / demo / paper / production trading path.
- Telegram Bot API remains refused.
- HITL does not skip PM4.
- `SIM-*` is never broker truth.
- Committed records are immutable; corrections are new events.

## 7. Correction-wave completion (2026-08-30)

| Step | Prompt requirement | Result |
|---|---|---|
| 1 | Reclassify operator as Seq 13; freeze; SEQUENCE_CORRECTION | **Done.** Freeze lifted after 09–12 gates in this same wave. |
| 2 | Seq 09 persistence | **Done.** 12/12 gate tests. |
| 3 | Seq 10 migrations/backup/recovery | **Done.** 5/5 + reproduced restart drill logs. |
| 4 | Seq 11 Demo MT5 + exit | **Done.** 6/6; live CLI fail-closed. Real terminal **BLOCKED** (no MT5 on host). |
| 5 | Seq 12 orchestrator | **Done.** 2/2. |
| 6 | Seq 13 reuse operator | **Done.** Bound to PersistenceApiV1; Telegram still refused. |

Full suite: **480 passed**. Sequence 14+ is **BLOCKED** pending architect review.

