# BotModuleProject1

Institutional modular Forex system for **MT5 Demo**, EURUSD first.

This repository is in **Sequence 03 — PM2 Market Context Engine**. It is **not** ready for demo trading, paper trading, or production. Live trading is disabled by design.

Git home: [scfrlight/GrokBuildapprepoFX](https://github.com/scfrlight/GrokBuildapprepoFX)

## Safety defaults

| Key | Value |
|---|---|
| Profile | `demo` (test/backtest/research allowed; `live` refused) |
| `BOTMODULEPROJECT1_SAFETY__TRADING_MODE` | `demo` |
| `BOTMODULEPROJECT1_SAFETY__LIVE_TRADING_ENABLED` | `false` |
| Feature flags | all `false`; dangerous flags are env-only |
| `enable_pm2_market_data` | `false` in YAML; test/research env opt-in only |
| Secrets in git | never |
| Python | 3.11+ (fail-fast; ADR-008) |

Unknown state, stale data, incomplete recovery, or ledger inconsistency must later force **safe halt / observe-only**.

CLI mode `live` and profile `live` are **recognized then refused**. Demo is a venue label, not permission to trade.

Unprefixed ambient env (`DATABASE_URL`, `TRADING_MODE`, …) is ignored.

## What exists now

- Architecture baseline, dependency graph, runtime-mode policy, ADRs 001–008
- Profiles: demo / test / backtest / research / live (blocked)
- pydantic-settings with prefix `BOTMODULEPROJECT1_`, secret allowlist, redaction
- Typed feature flags + startup preflight (`preflight_checked` lifecycle state)
- Versioned domain contracts in `botmoduleproject1/contracts/v1/` (schema 1.0.0), including PM2 outputs
- PM1 composition root: settings, registry, lifecycle, health, diagnostics, CLI
- PM2 market context: synthetic confirmed bars, regime, confluence, ranking, suppression, publication
- Fail-closed stubs: `NullRiskGate` always DENY, `DisabledExecution` raises
- Architecture console in the App Builder preview (read-only; not a trading UI)

## What does not exist yet

Trading strategies, TradeIntent generation, QRF/ML, risk math, order sending, real MT5 connection, Telegram bot, database schema, migrations.

PM2 is a ranking/context layer. It does not trade.

## Local onboarding (safe)

Requires Python 3.11+. Do not install the `mt5` extra on Linux.

```text
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env          # leave secrets empty; never commit
PYTHONPATH=. python -m botmoduleproject1 doctor --profile test --config configs/test.example.yaml
PYTHONPATH=. python -m pytest tests
```

PM2 opt-in (test profile only):

```text
BOTMODULEPROJECT1_FEATURE__ENABLE_PM2_MARKET_DATA=true PYTHONPATH=. python -m botmoduleproject1 doctor --profile test --config configs/test.example.yaml
```

Do **not** connect MetaTrader 5. Do **not** put tokens in `.env` until PM9/PM5 are in scope.

`python -m botmoduleproject1 live` must fail closed.

Windows: `scripts\bot\start.bat doctor --profile test --config configs\test.example.yaml`

## Next step

**Sequence 04 — PM3-Strategy Engine.**

Read:

- `docs/architecture/sequence_03_report.md`
- `docs/prompts/PM1_Sequence03_PM2_MarketContext_Prompt.md`
- `docs/architecture/bootstrap_governance.md`
