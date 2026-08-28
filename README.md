# BotModuleProject1

Institutional modular Forex system for **MT5 Demo**, EURUSD first.

This repository is in **Sequence 04 — PM3-Strategy Engine**. It is **not** ready for demo trading, paper trading, or production. Live trading is disabled by design.

Git home: [scfrlight/GrokBuildapprepoFX](https://github.com/scfrlight/GrokBuildapprepoFX)

## Safety defaults

| Key | Value |
|---|---|
| Profile | `demo` (test/backtest/research allowed; `live` refused) |
| Feature flags | all `false`; PM2 and PM3-Strategy Engine opt-in only in test/research |
| Secrets in git | never |
| Python | 3.11+ (fail-fast; ADR-008) |

The **PM3-Strategy Engine** emits analytical `TradeIntent` / `NoTradeDecision` only. That is not an order. PM4 still DENYs. PM5 still raises.

Unprefixed ambient env (`DATABASE_URL`, `TRADING_MODE`, …) is ignored.

## What exists now

- Sequences 01–03 kernel: PM1 platform, PM2 ranking/context (flag off in YAML)
- PM3-Strategy Engine: templates, profiles, pipes, consensus, TradeIntent (flag off in YAML)
- Fail-closed stubs: `NullRiskGate` always DENY, `DisabledExecution` raises
- Architecture console in the App Builder preview (read-only; not a trading UI)

## What does not exist yet

QRF/ML, risk math, order sending, MT5 connection, Telegram bot, database schema, migrations.

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

**Sequence 05 — PM3 Forecasting / QRF Research-to-Inference Pipeline.**
