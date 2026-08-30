# Decimal financial types

Accounting-sensitive keys (`price`, `qty`, `notional`, PnL, fees, spread, slippage, …) must be `Decimal` or canonical strings.

- Float, NaN, Infinity are rejected (`MoneyError`).
- Scale: 8 decimal places, `ROUND_HALF_EVEN`.
- SQLite stores canonical strings. PostgreSQL maps money columns to `NUMERIC(28, 8)`. `production_durable` remains refused.
- `PersistenceApiV1.persist_order` / `persist_execution` / `persist_signal` sanitize payloads.
- Positions projection `qty` / `avg_px` are canonical strings.

Residual non-money floats outside these keys remain PARTIAL.
