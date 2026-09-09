# Readiness

See [observability/health_readiness.md](./observability/health_readiness.md).

`trading_readiness` / `accept_trade` are **fail-closed by default**. Sequence 14 observe path cannot open them.

Sequence 15 Phase 1 introduces an explicit **DEMO-only allowlist** (`enable_demo_trading_readiness` env opt-in, demo profile, recovery/integrity/freshness). LIVE, paper, and production remain refused. Real MT5, mobile BFF, and live/production defaults are not wired.

The system is NOT ready for live trading, paper trading, or production.
