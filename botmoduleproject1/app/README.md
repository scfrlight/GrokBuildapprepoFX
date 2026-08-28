# `app` — PM1 composition root

Implemented in Sequence 01:

- `settings.py` — typed config, fingerprint, live-disabled fail-fast
- `bootstrap.py` / `container.py` / `runtime.py` — composition root
- `registry.py` / `lifecycle.py` / `health.py` — kernel services
- `contracts.py` — provider Protocols (not domain schemas)
- `stubs.py` — fail-closed placeholders (no MT5, no orders)

Must not contain strategy math, risk sizing, or broker calls.
