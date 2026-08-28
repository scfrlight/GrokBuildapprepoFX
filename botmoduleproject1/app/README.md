# `app` — PM1 composition root

Implemented in Sequence 01, extended in Sequence 02, wires PM2 in Sequence 03,
the PM3-Strategy Engine in Sequence 04, and PM3 forecasting / QRF in Sequence 05:

- `settings.py` — pydantic-settings, `BOTMODULEPROJECT1_` prefix, fingerprint, `pm2`, `pm3_strategy_engine`, and `pm3_forecasting` sections
- `profiles.py` / `feature_flags.py` / `preflight.py` / `python_version.py` / `secrets.py`
- `bootstrap.py` / `container.py` / `runtime.py` — composition root
- `registry.py` / `lifecycle.py` / `health.py` — kernel services (`preflight_checked`)
- `contracts.py` — provider Protocols (not domain schemas)
- `stubs.py` — fail-closed placeholders (no MT5, no orders)

When `enable_pm2_market_data` is env-opted in test/research, the container binds
`PM2Module` instead of `NullMarketData`. When `enable_pm3_strategy_engine` is
env-opted in test/research, it binds `PM3StrategyEngineModule` instead of
`NullSignals`. When `enable_forecasting` is env-opted in demo/test/research, it
binds `PM3ForecastingModule` instead of `NullModel`. Otherwise the placeholders
stay. No flag creates execution capability.

Must not contain strategy math as the composition root, risk sizing, or broker calls.
The PM3-Strategy Engine lives in `modules/pm3_strategy_engine/`.
PM3 forecasting / QRF lives in `modules/pm3_forecasting/`.
