# BotModuleProject1

Institutional modular Forex system for **MT5 Demo**, EURUSD first.

This repository is in **Sequence 00 — architecture baseline**. It is **not** ready for demo trading, paper trading, or production. Live trading is disabled by design.

Git home: [scfrlight/GrokBuildapprepoFX](https://github.com/scfrlight/GrokBuildapprepoFX)

## Safety defaults

| Key | Value |
|---|---|
| `TRADING_MODE` | `demo` |
| `LIVE_TRADING_ENABLED` | `false` |
| Feature flags | all `false` |
| Secrets in git | never |

Unknown state, stale data, incomplete recovery, or ledger inconsistency must later force **safe halt / observe-only**. That invariant is documented now and enforced in later sequences.

## What exists now

- Architecture baseline, dependency graph, runtime-mode policy
- ADRs 001–007
- Safe config templates (`.env.example`, `configs/*.example.yaml`)
- Empty Python package skeleton (`botmoduleproject1/`) with no business logic
- Architecture console in the App Builder preview (read-only; not a trading UI)

## What does not exist yet

Trading strategies, indicators, TradeIntent generation, QRF/ML, risk math, order sending, MT5 connection, Telegram bot, database schema, migrations.

## Normalized module map

| File (when added) | Function | Package |
|---|---|---|
| `PM1_Master_Prompt.md` | Platform bootstrap, DI, lifecycle | `botmoduleproject1.app` |
| `PM2_Master_Prompt.md` | Market data, session, regime | `modules.pm2_market_context` |
| `PM3_Strategy_Engine_Master_Prompt.md` | **PM3-Strategy Engine**, TradeIntent | `modules.pm3_strategy_engine` |
| `PM3_Master_Prompt.md` | Forecasting / QRF (not Strategy Engine) | `modules.pm3_forecasting` |
| `PM4_Master_Prompt.md` | Risk gate (exclusive) | `modules.pm4_risk` |
| `PM5_Master_Prompt.md` | MT5 OMS/EMS | `modules.pm5_execution` |
| `PM6_Master_Prompt.md` | Surveillance | `modules.pm6_monitoring` |
| `PM7_Master_Prompt.md` | Ledger / evidence | `modules.pm7_ledger` |
| `PM8_Master_Prompt.md` | Persistence / recovery | `modules.pm8_persistence` |
| `PM8a_Build_Spec.md` | PM8 build spec (not a module) | — |
| `PM9_…Telegram…` | Operator control plane | `modules.pm9_operator_ux` |
| `PM9a_…Studio…` | Fine-tune studio (operator layer) | `modules.pm9_operator_ux` |

Master prompt files were not present at Sequence 00. Place them in `docs/prompts/` before Sequence 01 if they become available.

## Local onboarding (safe)

Requires Python 3.11+. Do not install the `mt5` extra on Linux.

```text
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env          # leave secrets empty
```

Do **not** connect MetaTrader 5. Do **not** put tokens in `.env` until PM9/PM5 are in scope.

## Next step

**Sequence 01 — Contract-First Domain Foundation / PM1.**

Read:

- `docs/architecture/architecture_baseline.md`
- `docs/architecture/dependency_graph.md`
- `docs/architecture/runtime_modes.md`
- `docs/architecture/sequence_00_report.md`
- `docs/adr/`
