# BotModuleProject1

Institutional modular Forex system for **MT5 Demo**, EURUSD first.

This repository is in **Sequence 05 — PM3 forecasting / QRF**. It is **not** ready for demo trading, paper trading, or production. Live trading is disabled by design.

Git home: [scfrlight/GrokBuildapprepoFX](https://github.com/scfrlight/GrokBuildapprepoFX)

## Safety defaults

| Key | Value |
|---|---|
| Profile | `demo` (test/backtest/research allowed; `live` refused) |
| Feature flags | all `false`; PM2, PM3-Strategy Engine, and PM3 forecasting / QRF opt-in only via env |
| Secrets in git | never |
| Python | 3.11+ (fail-fast; ADR-008) |

The **PM3-Strategy Engine** emits analytical `TradeIntent` / `NoTradeDecision` only. **PM3 forecasting / QRF** may attach a `ForecastOutput` uncertainty envelope. Neither is an order. PM4 still DENYs. PM5 still raises.

Unprefixed ambient env (`DATABASE_URL`, `TRADING_MODE`, …) is ignored.

## What exists now

- Sequences 01–03 kernel: PM1 platform, PM2 ranking/context (flag off in YAML)
- PM3-Strategy Engine: templates, profiles, pipes, consensus, TradeIntent (flag off in YAML)
- PM3 forecasting / QRF: residual quantile envelope research kernel (flag off in YAML; not a fitted QRF)
- Fail-closed stubs: `NullRiskGate` always DENY, `DisabledExecution` raises
- Architecture console in the App Builder preview (read-only; not a trading UI)

## What does not exist yet

Fitted QRF/ML, risk math, order sending, MT5 connection, Telegram bot, database schema, migrations.

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

**Sequence 06 — PM4 Risk Gate.**

The system is NOT ready for live trading, demo trading, paper trading, or production.
