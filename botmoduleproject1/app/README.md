# `app` — PM1 composition root

Implemented in Sequence 01, extended in Sequence 02, wires PM2 in Sequence 03:

- `settings.py` — pydantic-settings, `BOTMODULEPROJECT1_` prefix, fingerprint, `pm2` section
- `profiles.py` / `feature_flags.py` / `preflight.py` / `python_version.py` / `secrets.py`
- `bootstrap.py` / `container.py` / `runtime.py` — composition root
- `registry.py` / `lifecycle.py` / `health.py` — kernel services (`preflight_checked`)
- `contracts.py` — provider Protocols (not domain schemas)
- `stubs.py` — fail-closed placeholders (no MT5, no orders)

When `enable_pm2_market_data` is env-opted in test/research, the container binds
`PM2Module` instead of `NullMarketData`. Otherwise the placeholder stays.

Must not contain strategy math, risk sizing, or broker calls.
