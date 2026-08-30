# CI

See [guides/ci.md](./guides/ci.md). Workflow: `.github/workflows/tests.yml`.

Sequence 14 forbids false-green gates: `pytest | tee`, `command | grep`, `command | tee | grep`. Pytest exit code is captured explicitly. Evidence artifacts upload after `success()`.

The system is NOT ready for live trading, demo trading, paper trading, or production.
