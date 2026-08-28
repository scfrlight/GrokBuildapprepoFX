# BotModuleProject1

Institutional modular Forex system for **MT5 Demo**, EURUSD first.

This repository is in **Sequence 02 — Configuration, Secrets & Bootstrap Governance**. It is **not** ready for demo trading, paper trading, or production. Live trading is disabled by design.

Git home: [scfrlight/GrokBuildapprepoFX](https://github.com/scfrlight/GrokBuildapprepoFX)

## Safety defaults

| Key | Value |
|---|---|
| Profile | `demo` (test/backtest/research allowed; `live` refused) |
| `BOTMODULEPROJECT1_SAFETY__TRADING_MODE` | `demo` |
| `BOTMODULEPROJECT1_SAFETY__LIVE_TRADING_ENABLED` | `false` |
| Feature flags | all `false`; dangerous flags are env-only |
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
- Versioned domain contracts in `botmoduleproject1/contracts/v1/` (schema 1.0.0)
- PM1 composition root: settings, registry, lifecycle, health, diagnostics, CLI
- Fail-closed stubs: `NullRiskGate` always DENY, `DisabledExecution` raises
- Architecture console in the App Builder preview (read-only; not a trading UI)

## What does not exist yet

Trading strategies, indicators, TradeIntent generation, QRF/ML, risk math, order sending, MT5 connection, Telegram bot, database schema, migrations.

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

Do **not** connect MetaTrader 5. Do **not** put tokens in `.env` until PM9/PM5 are in scope.

`python -m botmoduleproject1 live` must fail closed.

Windows: `scripts\bot\start.bat doctor --profile test --config configs\test.example.yaml`

## Next step

**Sequence 03 — PM2 Market Data & Session Regime Engine.**

Read:

- `docs/architecture/bootstrap_governance.md`
- `docs/architecture/sequence_02_report.md`
- `docs/adr/ADR-008-python-version-constraint.md`
