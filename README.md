# BotModuleProject1

Institutional modular Forex system for **MT5 Demo**, EURUSD first.

This repository is in **Sequence 09 — PM7 Persistence, Event Ledger, Reconciliation Store & Durable Audit Layer**. It is **not** ready for demo trading, paper trading, or production. Live trading is disabled by design.

Git home: [scfrlight/GrokBuildapprepoFX](https://github.com/scfrlight/GrokBuildapprepoFX)

## Safety defaults

| Key | Value |
|---|---|
| Profile | `demo` (test/backtest/research allowed; `live` refused) |
| Feature flags | all `false`; PM2–PM7 opt-in only via env (test/research) |
| Secrets in git | never |
| Python | 3.11+ (fail-fast; ADR-008) |

**PM4** is the authoritative risk gate. **PM5** is the OMS/EMS fabric (simulation/shadow; `SIM-*` is not a venue ticket). **PM6** is continuous post-trade monitoring. **PM7** is the append-only journal of those facts. It never sends orders, never sizes risk, never ALLOWs, and never calls MT5. Reconciliation without a venue stays **degraded**. Memory/file/SQLite are not production durability. `DisabledExecution` / `NullMonitoring` / `NullLedger` remain the default binds.

Unprefixed ambient env (`DATABASE_URL`, `TRADING_MODE`, …) is ignored.

## What exists now

- Sequences 01–05 kernel (flags off in YAML)
- PM4 Risk Gate (flag off; `NullRiskGate` when off)
- PM5 Execution OMS/EMS simulation (flag off; `DisabledExecution` when off)
- PM6 Post-Trade (flag off; `NullMonitoring` when off)
- **PM7 Persistence**: append-only journal, evidence, replay, integrity chain, retention freeze (flag off; `NullLedger` when off)
- Architecture console in the App Builder preview (read-only; not a trading UI)

## What does not exist yet

Fitted QRF/ML, real order sending, MT5 connection, Telegram bot, production distributed database, schema migrations, production-grade durability.

## Durable journal (Sequence 09)

- **Append-only.** Committed records are immutable. Corrections are new events linked by `causation_id`.
- **Truth.** `SIM-*` maps to `pm5_simulation`. Labelling it `pm5_broker` is rejected.
- **Reconciliation.** No venue → store `degraded` / `unavailable`. Never a silent pass. Later resolution is a new record.
- **Integrity.** SHA-256 hash chain is **tamper detection**, not tamper-proof storage. Mismatch is `compromised`; repair is a correction event.
- **Modes.** `disabled` (`NullLedger`), `memory` (default when flag on), `file_backed`, `sqlite_local`, `durable_candidate` (sqlite alias). `production_durable` is refused.
- **Retention.** Legal/audit freeze blocks purge. Test mode may simulate archival without deleting source data.
- **Queries.** Require `actor` + `authorized=true`. Exports strip secret-shaped keys.

Enabling `enable_pm7_persistence` in test/research still cannot send a broker order or treat `SIM-*` as MT5.

## Local onboarding (safe)

Requires Python 3.11+. Do not install the `mt5` extra on Linux.

```text
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
PYTHONPATH=. python -m botmoduleproject1 doctor --profile test --config configs/test.example.yaml
PYTHONPATH=. python -m pytest tests
```

`python -m botmoduleproject1 live` must fail closed.

## Next step

**Sequence 10 — PM8 Operator Control Plane, Telegram Control Engine & Human-in-the-Loop Operations.**

The system is NOT ready for live trading, demo trading, paper trading, or production.
