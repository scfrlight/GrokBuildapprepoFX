# PM3 forecasting / QRF

Full name is **PM3 forecasting / QRF**. Do not shorten to “PM3” in code or docs.
This package is **not** the PM3-Strategy Engine.

Research-to-inference kernel: a deterministic **residual quantile envelope**
over confirmed synthetic bars. A fitted sklearn Quantile Regression Forest is
out of scope for Sequence 05; later sequences may swap the estimator behind
the same `ModelProvider` port.

Produces `ForecastOutput` linked to an existing `TradeIntent` by `intent_id`.
Must not create intents, mutate side, size lots, emit `OrderRequest`, or call
PM4 / PM5 / MT5 / Telegram.

Feature flag `enable_forecasting` stays **false in YAML**. Env opt-in only via
`BOTMODULEPROJECT1_FEATURE__ENABLE_FORECASTING=true` (demo / test / research).
