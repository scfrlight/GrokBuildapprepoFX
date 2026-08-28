# ADR-010 — PM3 forecasting / QRF research kernel

Status: Accepted  
Date (UTC): 2026-08-28  
Sequence: 05

## Context

Sequence 05 adds uncertainty enrichment for an existing `TradeIntent`. The repository already reserved `pm3_forecasting` for **PM3 forecasting / QRF**, distinct from the **PM3-Strategy Engine**. A fitted sklearn Quantile Regression Forest is not available as a hard dependency and must not be faked. Forecasts must not become orders.

## Decision

1. **Naming.** The module is **PM3 forecasting / QRF** (`pm3_forecasting`). It is never shortened to “PM3”. It does not own strategy votes or `TradeIntent` creation.

2. **Enrichment only.** `ForecastOutput` links to an intent by `intent_id`. It does not mutate `direction`, carry lot size, or produce `OrderRequest`. Only a future PM4 `RiskVerdict.status == ALLOW` may unlock PM5.

3. **Honest estimator.** Sequence 05 ships a deterministic residual quantile envelope (empirical type-7 percentiles of embargoed walk-forward simple returns, mapped to price). A fitted QRF is out of scope; the envelope sits behind `ModelProvider` so a later sequence can swap it.

4. **Fail-closed.** Flag off → `NullModel` returns `None`. Insufficient history, lookahead, malformed bars, missing symbol, naive datetime, or unordered quantiles return `None`. YAML `enable_forecasting` stays false; env opt-in only.

5. **In-memory registry and conformal tracker.** Not durable (ADR-005). Insufficient conformal samples ≠ healthy. The module is non-critical.

## Consequences

- Downstream Sequence 06 (PM4 Risk Gate) may read `ForecastOutput`; this module must not bypass that gate.
- Operators must not treat a quantile envelope as a direction vote or a broker instruction.
- Replacing the envelope with a fitted QRF later must not change `ModelProvider.forecast(intent) -> ForecastOutput | None`.
