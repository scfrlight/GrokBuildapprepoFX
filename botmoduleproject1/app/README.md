# `app` — PM1 composition root

Implemented in Sequence 01, extended in Sequence 02:

- `settings.py` — pydantic-settings, `BOTMODULEPROJECT1_` prefix, fingerprint
- `profiles.py` / `feature_flags.py` / `preflight.py` / `python_version.py` / `secrets.py`
- `bootstrap.py` / `container.py` / `runtime.py` — composition root
- `registry.py` / `lifecycle.py` / `health.py` — kernel services (`preflight_checked`)
- `contracts.py` — provider Protocols (not domain schemas)
- `stubs.py` — fail-closed placeholders (no MT5, no orders)

Must not contain strategy math, risk sizing, or broker calls.
