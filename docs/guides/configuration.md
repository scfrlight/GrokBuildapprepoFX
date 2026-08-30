# Configuration guide

YAML under `configs/`. Feature flags default **false**. Unprefixed ambient env is ignored. Secrets only from the allowlist (`app/secrets.py`).

Live profile, `cli_mode=live`, and `LIVE_TRADING_ENABLED` fail closed.

See `docs/architecture/runtime_modes.md` and ADR-006.
