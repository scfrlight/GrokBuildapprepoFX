# `contracts` — versioned integration language

Current schema: **v1** (`botmoduleproject1.contracts.v1`).

Namespaces:

- `strategy` — **PM3-Strategy Engine** (`TradeIntent`, …)
- `forecasting` — PM3 QRF / uncertainty (`ForecastOutput`, …)

These are different modules. Do not merge them.

UTC-first. Naive datetime is rejected. Commands carry `idempotency_key`.
`OrderRequest.risk_verdict_id` is required (ADR-007).
