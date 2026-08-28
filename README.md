# BotModuleProject1

Institutional modular Forex system for **MT5 Demo**, EURUSD first.

This repository is in **Sequence 08 — PM6 Post-Trade Controls**. It is **not** ready for demo trading, paper trading, or production. Live trading is disabled by design.

Git home: [scfrlight/GrokBuildapprepoFX](https://github.com/scfrlight/GrokBuildapprepoFX)

## Safety defaults

| Key | Value |
|---|---|
| Profile | `demo` (test/backtest/research allowed; `live` refused) |
| Feature flags | all `false`; PM2–PM6 opt-in only via env (test/research) |
| Secrets in git | never |
| Python | 3.11+ (fail-fast; ADR-008) |

**PM4** is the authoritative risk gate. **PM5** is the OMS/EMS fabric (simulation/shadow; `SIM-*` is not a venue ticket). **PM6** is continuous post-trade monitoring: two defence lanes, surveillance, incidents, withdrawal plans, and non-durable audit evidence. It never sends orders. Reconciliation without a venue stays **degraded**. `DisabledExecution` / `NullMonitoring` remain the default binds.

Unprefixed ambient env (`DATABASE_URL`, `TRADING_MODE`, …) is ignored.

## What exists now

- Sequences 01–05 kernel (flags off in YAML)
- PM4 Risk Gate (flag off; `NullRiskGate` when off)
- PM5 Execution OMS/EMS simulation (flag off; `DisabledExecution` when off)
- **PM6 Post-Trade**: monitoring, surveillance, incidents, governance (flag off; `NullMonitoring` when off)
- Architecture console in the App Builder preview (read-only; not a trading UI)

## What does not exist yet

Fitted QRF/ML, real order sending, MT5 connection, Telegram bot, database schema, migrations, durable event ledger.

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

PM6 observes PM4/PM5. Enabling `enable_pm6_post_trade` in test/research still cannot send a broker order or treat `SIM-*` as MT5.

## Next step

**Sequence 09 — PM7 Persistence, Event Ledger, Reconciliation Store & Durable Audit Layer.**

The system is NOT ready for live trading, demo trading, paper trading, or production.
