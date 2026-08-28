# BOTMODULEPROJECT1 — SEQUENCE 05
# PM3 forecasting / QRF Research-to-Inference Pipeline

Persisted source-of-truth for Sequence 05. Original filename `PM3_Master_Prompt.md` was not found on Drive/GitHub; this document is the complete Sequence 05 specification as executed on 2026-08-28.

Display name is always **PM3 forecasting / QRF**. Never shorten to “PM3”. This package is **not** the PM3-Strategy Engine (`modules.pm3_strategy_engine`).

Git home: `scfrlight/GrokBuildapprepoFX`. Sequence 04 kernel is complete (159 tests). This sequence implements the forecasting research-to-inference kernel only.

==================================================
0. CRITICAL NAMING AND SAFETY
==================================================

Packages stay separate:

1. **PM3-Strategy Engine** — templates, profiles, pipes, consensus, `TradeIntent`.
2. **PM3 forecasting / QRF** — uncertainty enrichment, quantiles, residual envelope, conformal coverage.

Forecasts **enrich uncertainty**. They never:

- create a `TradeIntent`;
- mutate `direction` / side;
- produce `OrderRequest`;
- size lots;
- call MT5 or Telegram;
- bypass PM4.

Legal future path:

```text
PM2 context → PM3-Strategy Engine TradeIntent
  → PM3 forecasting / QRF enrichment (ForecastOutput)
  → PM4 RiskVerdict ALLOW
  → PM5 Execution
```

Non-negotiable:

- Feature flag `enable_forecasting` stays **false in YAML**.
- Env opt-in only: `BOTMODULEPROJECT1_FEATURE__ENABLE_FORECASTING=true`.
- Allowed profiles remain catalogued (demo / test / research). YAML cannot be treated as the enable path.
- No sklearn, numpy, pandas, MetaTrader5, telegram as hard dependencies. stdlib + existing pydantic/decimal.
- No live / demo / paper order sending. Runtime remains NOT trade-ready.
- Do not import `modules.pm3_strategy_engine` internals, `pm4_risk`, `pm5_execution`, `adapters.mt5`, `adapters.telegram`.
- Synthetic confirmed bars only, via `botmoduleproject1.adapters.market.synthetic` (public adapter). Confirmed bars end before `as_of`.
- Python 3.11+ floor stays. Tests already patch `interpreter_version` in `conftest.py`.

==================================================
1. EXISTING CONTRACTS (DO NOT FORK)
==================================================

`botmoduleproject1/contracts/v1/forecasting.py` already has:

- `QuantileSet(q05, q25, q50, q75, q95)` Decimal
- `ModelVersionInfo(model_id, version, trained_at, registry_uri)`
- `ForecastOutput(forecast_id, intent_id, event_id, correlation_id, causation_id, occurred_at, symbol, horizon_bars, quantiles, model, producer="pm3_forecasting")`

Extend backward-compatibly:

- Add a `model_validator` on `QuantileSet`: `q05 <= q25 <= q50 <= q75 <= q95` (non-decreasing; equals allowed).
- Optional enrichment fields on `ForecastOutput` if needed (`coverage`, `sample_size`, `horizon_seconds`, `diagnostics` dict). Keep frozen `extra=forbid`; add explicit fields only.
- Do **not** add forecast fields onto `TradeIntent`. Link by `intent_id`.

`ModelProvider` in `app/contracts.py`:

```python
def forecast(self, intent: TradeIntent) -> ForecastOutput | None
```

Keep this signature. Module may also expose `forecast_with_bars(intent, bars)` for tests.

`NullModel` in `stubs.py` currently returns `None`. Keep `NullModel` as the flag-off path.

==================================================
2. ESTIMATOR (HONEST — NOT A FAKE TRAINED FOREST)
==================================================

Implement a **deterministic residual quantile envelope** as the research kernel.

A fitted sklearn Quantile Regression Forest is **OUT OF SCOPE** for Sequence 05. This is the research-to-inference plumbing with a nonparametric estimator that a later sequence can swap for a fitted QRF.

Algorithm:

1. Take confirmed OHLCV bars for `intent.symbol` (`SyntheticMarketFeed` / `generate_bars`). Default timeframe H1, lookback >= 64, `horizon_bars` default 4.
2. Close-to-close simple returns `r[t] = close[t]/close[t-1] - 1`. Never use a bar whose `open_time >= as_of`. Never use the forming bar.
3. Walk-forward with embargo: for training sample at index `i`, forward return uses `close[i+horizon]/close[i] - 1`, and inference at time `T` may only use samples with `(i+horizon) < T` (no lookahead). Embargo at least 1 bar.
4. Empirical quantiles of those historical forward returns: 0.05, 0.25, 0.50, 0.75, 0.95. Use a deterministic percentile (linear interpolation between sorted samples; Hyndman-Fan type 7 / numpy `linear`). Need `min_samples` (default 20) else return `None`.
5. Map to price: `price_q = last_confirmed_close * (1 + q_return)`. Keep Decimal quantized to 5 decimal places for FX.
6. `q50` is the median residual path. It is **NOT** a direction vote. LONG and SHORT intents with the same bars MUST produce identical quantiles (side-invariance).
7. `ModelVersionInfo`: `model_id="residual_quantile_envelope"`, `version="0.1.0"`, `trained_at=as_of` (the research fit time, UTC), `registry_uri=None` unless in-memory registry assigns one.
8. Identity: forecast `event_id` new UUID; `correlation_id` copied from intent; `causation_id = intent.event_id`; `intent_id` copied; `producer="pm3_forecasting"`.
9. Idempotency: same `intent.idempotency_key` returns the same cached `ForecastOutput` (do not emit a second `forecast_id`).
10. Fail-closed → return `None` (do not raise into execution) when: flag conceptually off (`NullModel`), insufficient history, empty/malformed bars, unordered would-be quantiles, missing symbol, naive datetime, lookahead detected.

Conformal coverage tracker (in-memory): after each forecast, if a later confirmed bar arrives that realizes the horizon, record whether realized close was inside `[q05, q95]` and `[q25, q75]`. Health reports `sample_size` and empirical coverage. Insufficient data ≠ healthy.

In-memory model registry (not PM8): register the envelope model version. Not durable.

==================================================
3. MODULE LAYOUT
==================================================

```text
botmoduleproject1/modules/pm3_forecasting/
  README.md
  __init__.py
  module.py              # PM3ForecastingModule, from_settings, implements ModelProvider
  capabilities.py        # metadata, non-critical, FORECASTING capability
  contracts.py           # module-local ports if needed
  config/schema.py + defaults.py + __init__.py
  domain/enums.py, ids.py, policies.py
  features/returns.py    # confirmed-bar returns, no lookahead assert
  research/splitter.py   # walk-forward + embargo
  inference/envelope.py  # empirical quantiles → QuantileSet in price space
  inference/conformal.py # coverage tracker
  registry/memory.py     # in-memory ModelVersionInfo store
  application/enrichment.py  # intent → ForecastOutput
  diagnostics/health.py, readiness.py
  publication/publisher.py
```

Follow naming/style of `modules/pm2_market_context` and `modules/pm3_strategy_engine`. English only. No versioned class names (no v5, v8).

==================================================
4. INTEGRATION (PM1 COMPOSITION ROOT)
==================================================

1. `app/container.py`: add `_forecasting_module` like `_strategy_engine_module`. If `overrides["forecasting"]` use it; elif `settings.feature_flags.forecasting`: `PM3ForecastingModule.from_settings(settings, clock)`; else `NullModel()`.
2. `app/feature_flags.py`: update description of `enable_forecasting` from "Not implemented." to kernel description. Do NOT change `allowed_profiles` or make it YAML-enableable.
3. `app/settings.py`: add `Pm3ForecastingSection` nested model (`horizon_bars=4`, `lookback_bars=64`, `min_samples=20`, `embargo_bars=1`, `timeframe=H1`, `operating_mode=shadow`, `observe_only=True`). Field on Settings: `pm3_forecasting: Pm3ForecastingSection`.
4. `configs/base.example.yaml` + `configs/pm3_forecasting.example.yaml` (new). Flag stays false.
5. Update feature flag catalog description only.

==================================================
5. TESTS
==================================================

Add:

- `tests/contract/test_pm3_forecast_contracts.py` — QuantileSet ordering, ForecastOutput UTC, producer
- `tests/unit/test_pm3_fx_no_lookahead.py` — walk-forward does not use future bars
- `tests/unit/test_pm3_fx_side_invariance.py` — BUY vs SELL same bars → identical quantiles
- `tests/unit/test_pm3_fx_envelope.py` — ordered quantiles, Decimal 5dp, min_samples None
- `tests/unit/test_pm3_fx_idempotency.py` — duplicate idempotency_key
- `tests/unit/test_pm3_fx_flag.py` — flag off → NullModel None; flag on via override
- `tests/unit/test_pm3_fx_safety.py` — no OrderRequest, requested_volume stays None on intent, no PM5 import
- `tests/unit/test_pm3_fx_integration.py` — container wires module when flag on; health non-critical

Helper to build a TradeIntent: look at `tests/unit/pm3se_support.py` for patterns. `requested_volume` must be `None`.

Run: `PYTHONPATH=. python -m pytest tests` (sandbox is 3.10 with conftest patch). ALL existing 159 tests plus new ones must pass. Do not weaken existing tests.

==================================================
6. DOCS TO UPDATE
==================================================

- `docs/architecture/architecture_baseline.md` — Sequence 05 status
- `docs/architecture/dependency_graph.md` — forecasting module
- `docs/architecture/repository_assessment.md` — Sequence 05 inputs (prompt not recovered; persisted)
- `docs/adr/README.md` — ADR-010
- `docs/adr/ADR-010-pm3-forecasting-research-kernel.md`
- `docs/prompts/README.md`
- `README.md` — Sequence 05, next step Sequence 06 PM4 Risk. Repeat: NOT ready for live/demo/paper/production.
- `botmoduleproject1/modules/pm3_forecasting/README.md`
- `pyproject.toml` description bump to Sequence 05
- `docs/architecture/pm3_forecasting_integration_plan.md` (this sequence; written before the module)
- `docs/architecture/sequence_05_report.md`

==================================================
7. TRADING READINESS
==================================================

The system is NOT ready for live trading, demo trading, paper trading, or production.

Next step: Sequence 06 — PM4 Risk Gate.
