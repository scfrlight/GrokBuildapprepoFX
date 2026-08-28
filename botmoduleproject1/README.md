# Python package `botmoduleproject1`

Import root for the trading system.

Sequence 01: versioned contracts + PM1 composition root.
Sequence 02: profiles, pydantic-settings, feature flags, preflight.
Sequence 03: PM2 market context / ranking (feature-flag opt-in, test/research only).

CLI: `python -m botmoduleproject1 --profile test doctor`

Forbidden still: strategies, MT5 calls, Telegram, risk math, order send.
Not trade-ready. Live trading is disabled. Python 3.11+ required.
