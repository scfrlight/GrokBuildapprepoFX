# BotModuleProject1

Institutional modular Forex system for **MT5 Demo**, EURUSD first.

This repository is in **canonical Sequence 14 (observability / operations / documentation)** after the 2026-08-30 sequence correction and the Sequence 14 authorization. Historical “Sequence 10 / PM8 Operator” was an early build of Sequence 13. See [docs/SEQUENCE_CORRECTION.md](docs/SEQUENCE_CORRECTION.md) and [docs/MODULE_NUMBERING_MAP.md](docs/MODULE_NUMBERING_MAP.md).

It is **not** ready for demo trading, live trading, or production. Live trading is disabled by design.

Git home: [scfrlight/GrokBuildapprepoFX](https://github.com/scfrlight/GrokBuildapprepoFX)

## Safety defaults

| Key | Value |
|---|---|
| Profile | `demo` (test/backtest/research allowed; `live` refused) |
| Feature flags | all `false`; PM2–PM8 / Sequence 11–13 opt-in only via env (test/research) |
| Secrets in git | never |
| Python | 3.11+ (fail-fast; ADR-008) |
| Trading readiness | **false** (Sequence 14 cannot set it true) |

**PM4** is the authoritative risk gate. **PM5** is the OMS/EMS fabric (simulation/shadow; `SIM-*` is not a venue ticket). **Sequence 11** is `mt5_execution_engine` (tickets `DEMO-*`, not broker truth; not PM6). **PM6** is only `pm6_post_trade` (post-trade governance; not Seq 14). **PM7** is a **PARTIAL** append-only evidence-journal subset (not production durable, not the downstream API). **PM8 persistence** (canonical Sequences 09–10, **PARTIAL** vs reconstructed PM8a) is the only downstream data API. **PM8a** is the build-spec/hardening identity of that same package. **Operator** is Sequence 13; Telegram Bot API refused. **Sequence 14** is `modules/observability` (not PM6). Inventory: [docs/ARCHITECTURE_INVENTORY.md](docs/ARCHITECTURE_INVENTORY.md). PM8 gaps: [docs/PM8_PM8A_GAP_MATRIX.md](docs/PM8_PM8A_GAP_MATRIX.md).

Unprefixed ambient env (`DATABASE_URL`, `TRADING_MODE`, …) is ignored.

## Canonical sequence (after correction)

| Seq | Content | Default bind |
|---|---|---|
| 00–08 | Platform through PM6 post-trade (historical, kept) | flags off |
| **09** | PM8 database consolidation | `NullStorage` |
| **10** | PM8a migrations / backup / restore / restart drills | off |
| **11** | `mt5_execution_engine` (not PM6) | fail-closed / simulated tests |
| **12** | Unified runtime orchestrator | off |
| **13** | Operator UX (reused `pm8_operator`) | `NullOperator` |
| **14** | Observability / operations / documentation | always-on diagnostics; not a trade flag |

## Distinctions

- PM6 = `pm6_post_trade` (post-trade monitoring/governance). Sequence 14 observability is **not** PM6.
- Sequence 11 = `mt5_execution_engine` (Demo execution/exit **simulation**)
- PM7 = PARTIAL evidence-journal subset (sqlite/file now reload; not production durable; not the downstream API)
- PM8 = persistence/consolidation data API (`PersistenceApiV1`); named projections are rebuildable read models
- PM8a = implementation/hardening specification for PM8 (same package)
- Sequence 09 = PM8 consolidation
- Sequence 10 = PM8a hardening
- Sequence 13 = operator UX reuse
- Sequence 14 = observability/operations/documentation
- Durability remediation 2026-08-30 = SQLite local/test
- PostgreSQL durability 2026-08-30 = `PostgresStore` fail-closed backend (`production_durable` still refused)
- Sequence 15+ = **BLOCKED**

## What does not exist yet

Fitted QRF/ML, real MT5 terminal send on this Linux host, live Telegram bot, Sequence 15+.

PostgreSQL is an implemented PM8 backend, not a production-readiness claim. `production_durable` stays refused.

`python -m botmoduleproject1 live` must fail closed.

```text
PYTHONPATH=. python -m botmoduleproject1 observe --profile test --config configs/test.example.yaml --json
```

The system is NOT ready for live trading, demo trading, paper trading, or production.
