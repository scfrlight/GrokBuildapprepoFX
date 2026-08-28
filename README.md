# BotModuleProject1

Institutional modular Forex system for **MT5 Demo**, EURUSD first.

This repository is in **Sequence 07 — PM5 Execution & Broker Routing**. It is **not** ready for demo trading, paper trading, or production. Live trading is disabled by design.

Git home: [scfrlight/GrokBuildapprepoFX](https://github.com/scfrlight/GrokBuildapprepoFX)

## Safety defaults

| Key | Value |
|---|---|
| Profile | `demo` (test/backtest/research allowed; `live` refused) |
| Feature flags | all `false`; PM2–PM4 and PM5 simulation opt-in only via env |
| Secrets in git | never |
| Python | 3.11+ (fail-fast; ADR-008) |

The **PM3-Strategy Engine** emits analytical `TradeIntent` / `NoTradeDecision` only. **PM3 forecasting / QRF** may attach a `ForecastOutput` uncertainty envelope. **PM4** is the authoritative risk gate: deny-by-default, ALLOW is not an order. **PM5** is the OMS/EMS fabric: simulation/shadow only, PM4-only authorization, no real MT5 send. `DisabledExecution` remains the default bind. Reconciliation without a venue is degraded, never a silent pass.

Unprefixed ambient env (`DATABASE_URL`, `TRADING_MODE`, …) is ignored.

## What exists now

- Sequences 01–03 kernel: PM1 platform, PM2 ranking/context (flag off in YAML)
- PM3-Strategy Engine: templates, profiles, pipes, consensus, TradeIntent (flag off in YAML)
- PM3 forecasting / QRF: residual quantile envelope research kernel (flag off in YAML; not a fitted QRF)
- PM4 Risk Gate: admission, budgets, sizing, heat, concentration, drawdown, kill-switch (flag off in YAML)
- **PM5 Execution**: OMS lifecycle, simulation adapter, independent control plane, recon, surveillance (flag off in YAML; `DisabledExecution` when off)
- Architecture console in the App Builder preview (read-only; not a trading UI)

## What does not exist yet

Fitted QRF/ML, real order sending, MT5 connection, Telegram bot, database schema, migrations, durable execution ledger.

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

PM5 simulation is not a venue. Enabling `enable_pm5_simulation` in test/research still cannot send a broker order. `enable_pm5_broker_adapter`, `enable_mt5_demo_execution`, and `enable_live_execution` are refused.

## Next step

**Sequence 08 — PM6 Post-Trade, Reconciliation, Performance & Research Feedback Layer.**

The system is NOT ready for live trading, demo trading, paper trading, or production.
