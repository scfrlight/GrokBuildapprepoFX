# Module numbering map

Status: **Accepted** — architect follow-up 2026-08-30 (problems 2.1–2.4)  
Source of sequence **order**: Master Orchestration Prompt (file missing; order taken from the 2026-08-30 correction prompt)  
Source of package **names**: this file. Do not infer a package from a sequence title.

Bare **`pm6` is reserved for post-trade**. Sequence 11 is **`mt5_execution_engine`**.

## 1. Canonical map

| Seq | Canonical sequence name (Master Orchestration order) | PM\*_Master_Prompt / spec | Package in repo (actual = final) | Status |
|---|---|---|---|---|
| 00 | Repository reconnaissance | — | `docs/` | Done |
| 01 | PM1 platform kernel | `PM1_Master_Prompt.md` | `botmoduleproject1.app` | Done |
| 02 | Configuration governance | `PM1_Sequence02_Configuration_Governance_Prompt.md` | `app/settings.py`, `app/feature_flags.py` | Done |
| 03 | PM2 Market Context | `PM1_Sequence03_PM2_MarketContext_Prompt.md` | `modules/pm2_market_context` | Done |
| 04 | PM3 Strategy Engine | `PM3_Strategy_Engine_Sequence04_Prompt.md` | `modules/pm3_strategy_engine` | Done |
| 05 | PM3 Forecasting / QRF | `PM3_Forecasting_Sequence05_Prompt.md` | `modules/pm3_forecasting` | Done |
| 06 | PM4 Risk Gate | `PM4_Risk_Gate_Sequence06_Prompt.md` | `modules/pm4_risk_gate` | Done |
| 07 | PM5 OMS/EMS simulation | `PM5_Execution_Sequence07_Prompt.md` | `modules/pm5_execution` | Done |
| 08 | **PM6 Post-Trade Controls** | `PM6_Post_Trade_Sequence08_Prompt.md` | **`modules/pm6_post_trade`** | Done |
| 09 | **PM8 Database Consolidation** | reconstructed `PM8a_Build_Spec.md` | **`modules/pm8_persistence`** | Done |
| 10 | **PM8a Migration, Backup & Recovery** | reconstructed `PM8a_Build_Spec.md` | **`modules/pm8_persistence`** (v2 + runbooks) | Done |
| 11 | MT5 Execution & Exit Engine (Demo-only). *Master Orchestration title:* “PM6 MT5 Execution & Exit Engine” | original spec missing | **`modules/mt5_execution_engine`** + adapter `adapters/mt5` | Done |
| 12 | Unified Runtime Orchestrator | correction prompt | `botmoduleproject1/runtime` | Done |
| 13 | PM9 Operator UX & Telegram Control | `PM8_Operator_Sequence10_Prompt.md` (historical filename) | `modules/pm8_operator` (re-export `pm9_operator_ux`) | Done |

No row uses a second package whose last path segment is bare `pm6`. There is no `modules/pm6_execution`.

## 2. Sequence 11 naming (the PM6 collision)

| Field | Value |
|---|---|
| Master Orchestration **title** | PM6 MT5 Execution & Exit Engine |
| Why that title is unsafe as a package | Sequence 08 already shipped **`pm6_post_trade`** for PM6_Master_Prompt (monitoring, incidents, withdrawal). Two modules named `pm6*` would invite wiring MT5 execution to the surveillance package. |
| **Final package** | `botmoduleproject1.modules.mt5_execution_engine` |
| Adapter (transport only) | `botmoduleproject1.adapters.mt5` |
| Rejected names | `pm6`, `pm6_execution`, `pm5_execution.demo_routing` as the home of Seq 11 |
| What stayed | `pm6_post_trade` (Seq 08). `pm5_execution` (Seq 07, `SIM-*` only). Sequence 07 `Mt5BrokerAdapter` still blocked. |

Routing (`DemoRouter`) and exits (`ExitEngine`) **moved** from `pm5_execution` into `mt5_execution_engine`. Old import paths raise `ModuleNotFoundError`.

## 3. Sequence 09 — previous-session numbering error

**“Sequence 09 = PM7 journal” was an error of a previous session.**

| | Historical (wrong sequence number) | Canonical (this map) |
|---|---|---|
| Sequence 09 | PM7 append-only journal | **PM8 database consolidation** (`pm8_persistence`) |
| PM7 journal content | implemented under `modules/pm7_persistence` | **stays there** — it belongs in the PM1–PM7 range as **PM7**, not as Sequence 09 |
| Historical report | `docs/architecture/sequence_09_report.md` (banner: misnumbered) | kept for archaeology |
| Canonical report | — | `docs/architecture/sequence_09_pm8_consolidation_report.md` |

PM7 is not mixed into PM8. PM8 `PersistenceApiV1` is the only downstream data path after canonical Sequence 09. PM7 remains the evidence journal behind `enable_pm7_persistence` (default off, `NullLedger`).

Operator built as “Sequence 10” was the same class of error; that code is Sequence 13 / `pm8_operator`. Canonical Sequence 10 is PM8a hardening.

## 4. Compatibility re-exports (not second identities)

| Alias package | Points at | Note |
|---|---|---|
| `pm4_risk` | `pm4_risk_gate` | Seq 06 |
| `pm6_monitoring` | `pm6_post_trade` | Seq 08 — still PM6 post-trade |
| `pm7_ledger` | `pm7_persistence` | PM7, not Seq 09 |
| `pm9_operator_ux` | `pm8_operator` | Seq 13 |

These aliases must not be used to invent a second `pm6` execution module.

## 5. Feature flags (YAML default false)

| Flag | Package |
|---|---|
| `pm6_post_trade` | `pm6_post_trade` |
| `pm8_persistence` | `pm8_persistence` |
| `mt5_demo_adapter`, `exit_engine` | `mt5_execution_engine` |
| `pm8_operator` | `pm8_operator` (Seq 13) |

## 6. Imports (Sequence 11)

```python
from botmoduleproject1.modules.mt5_execution_engine import DemoRouter, ExitEngine
from botmoduleproject1.adapters.mt5 import DemoMt5Gateway
```
