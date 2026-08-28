# BotModuleProject1

Institutional modular Forex system for **MT5 Demo**, EURUSD first.

This repository is in **Sequence 06 — PM4 Risk Gate**. It is **not** ready for demo trading, paper trading, or production. Live trading is disabled by design.

Git home: [scfrlight/GrokBuildapprepoFX](https://github.com/scfrlight/GrokBuildapprepoFX)

## Safety defaults

| Key | Value |
|---|---|
| Profile | `demo` (test/backtest/research allowed; `live` refused) |
| Feature flags | all `false`; PM2, PM3-Strategy Engine, PM3 forecasting / QRF, and PM4 Risk Gate opt-in only via env |
| Secrets in git | never |
| Python | 3.11+ (fail-fast; ADR-008) |

The **PM3-Strategy Engine** emits analytical `TradeIntent` / `NoTradeDecision` only. **PM3 forecasting / QRF** may attach a `ForecastOutput` uncertainty envelope. **PM4** is the authoritative risk gate: deny-by-default, ALLOW is not an order. PM5 still raises.

Unprefixed ambient env (`DATABASE_URL`, `TRADING_MODE`, …) is ignored.

## What exists now

- Sequences 01–03 kernel: PM1 platform, PM2 ranking/context (flag off in YAML)
- PM3-Strategy Engine: templates, profiles, pipes, consensus, TradeIntent (flag off in YAML)
- PM3 forecasting / QRF: residual quantile envelope research kernel (flag off in YAML; not a fitted QRF)
- **PM4 Risk Gate**: admission, hierarchical budgets, uncertainty-aware sizing, heat, concentration, drawdown ladder, pre-trade controls, kill-switch (flag off in YAML; `NullRiskGate` when off)
- Fail-closed execution: `DisabledExecution` raises
- Architecture console in the App Builder preview (read-only; not a trading UI)

## What does not exist yet

Fitted QRF/ML, order sending, MT5 connection, Telegram bot, database schema, migrations, durable risk ledger.

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

PM4 output is a risk-governed handoff artifact, not a broker order. Enabling `enable_pm4_risk_gate` in test/research still cannot open PM5.

## Next step

**Sequence 07 — PM5 Execution & Broker Routing Layer.**

The system is NOT ready for live trading, demo trading, paper trading, or production.
