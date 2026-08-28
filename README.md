# BotModuleProject1

Institutional modular Forex system for **MT5 Demo**, EURUSD first.

This repository is in **Sequence 01 — Contract-First Domain Foundation + PM1 platform kernel**. It is **not** ready for demo trading, paper trading, or production. Live trading is disabled by design.

Git home: [scfrlight/GrokBuildapprepoFX](https://github.com/scfrlight/GrokBuildapprepoFX)

## Safety defaults

| Key | Value |
|---|---|
| `TRADING_MODE` | `demo` |
| `LIVE_TRADING_ENABLED` | `false` |
| Feature flags | all `false` |
| Secrets in git | never |

Unknown state, stale data, incomplete recovery, or ledger inconsistency must later force **safe halt / observe-only**. That invariant is documented now and enforced in later sequences.

CLI mode `live` is **recognized then refused** (exit code 2). Demo is a venue label, not permission to trade.

## What exists now

- Architecture baseline, dependency graph, runtime-mode policy, ADRs 001–007
- Safe config templates (`.env.example`, `configs/*.example.yaml`)
- Versioned domain contracts in `botmoduleproject1/contracts/v1/` (schema 1.0.0)
- PM1 composition root: settings, registry, lifecycle, health, diagnostics, CLI
- Fail-closed stubs: `NullRiskGate` always DENY, `DisabledExecution` raises
- Architecture console in the App Builder preview (read-only; not a trading UI)

## What does not exist yet

Trading strategies, indicators, TradeIntent generation, QRF/ML, risk math, order sending, MT5 connection, Telegram bot, database schema, migrations.

## Normalized module map

| File (when added) | Function | Package | Sequence |
|---|---|---|---|
| `PM1_Master_Prompt.md` | Platform bootstrap, DI, lifecycle | `botmoduleproject1.app` | **01 — kernel** |
| `PM2_Master_Prompt.md` | Market data, session, regime | `modules.pm2_market_context` | later |
| `PM3_Strategy_Engine_Master_Prompt.md` | **PM3-Strategy Engine**, TradeIntent | `modules.pm3_strategy_engine` | later |
| `PM3_Master_Prompt.md` | Forecasting / QRF (not Strategy Engine) | `modules.pm3_forecasting` | later |
| `PM4_Master_Prompt.md` | Risk gate (exclusive) | `modules.pm4_risk` | later |
| `PM5_Master_Prompt.md` | MT5 OMS/EMS | `modules.pm5_execution` | later |
| `PM6_Master_Prompt.md` | Surveillance | `modules.pm6_monitoring` | later |
| `PM7_Master_Prompt.md` | Ledger / evidence | `modules.pm7_ledger` | later |
| `PM8_Master_Prompt.md` | Persistence / recovery | `modules.pm8_persistence` | later |
| `PM8a_Build_Spec.md` | PM8 build spec (not a module) | — | later |
| `PM9_…Telegram…` | Operator control plane | `modules.pm9_operator_ux` | later |
| `PM9a_…Studio…` | Fine-tune studio (operator layer) | `modules.pm9_operator_ux` | later |

`docs/prompts/PM1_Master_Prompt.md` is the persisted Sequence 01 source of truth. Other PM files are still missing.

## Local onboarding (safe)

Requires Python 3.11+. Do not install the `mt5` extra on Linux.

```text
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env          # leave secrets empty
PYTHONPATH=. python -m botmoduleproject1 doctor --config configs/test.example.yaml
PYTHONPATH=. python -m pytest tests
```

Do **not** connect MetaTrader 5. Do **not** put tokens in `.env` until PM9/PM5 are in scope.

`python -m botmoduleproject1 live` must fail closed.

Windows: `scripts\bot\start.bat doctor --config configs\test.example.yaml`

## Next step

**Sequence 02 — Configuration, Secrets & Bootstrap Governance.**

Read:

- `docs/architecture/architecture_baseline.md`
- `docs/architecture/sequence_01_report.md`
- `docs/prompts/PM1_Master_Prompt.md`
- `docs/adr/`
