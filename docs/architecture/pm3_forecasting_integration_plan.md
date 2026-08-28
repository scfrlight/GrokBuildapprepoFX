# PM3 forecasting / QRF — Integration Plan (Sequence 05)

Status: Accepted before implementation  
Date (UTC): 2026-08-28  
Package: `botmoduleproject1.modules.pm3_forecasting`  
Display name: **PM3 forecasting / QRF** (never shortened to “PM3”)

This plan is the gate for Sequence 05. Implementation follows it; it does not authorize trading. A fitted sklearn Quantile Regression Forest is out of scope.

---

## 1. Naming collision

| Name | Package | Owns | Must not own |
|---|---|---|---|
| **PM3-Strategy Engine** | `modules.pm3_strategy_engine` | templates, profiles, pipes, consensus, TradeIntent, NoTradeDecision | QRF, quantiles, forecasts |
| **PM3 forecasting / QRF** | `modules.pm3_forecasting` | residual quantile envelope, ForecastOutput, conformal coverage, in-memory model registry | strategy votes, TradeIntent creation, side mutation, orders |

Kernel placeholders stay distinct: `NullSignals` (strategy engine) vs `NullModel` (this module). Comments, class names, variables, docs, and the Sequence 05 report always write **PM3 forecasting / QRF**.

---

## 2. Inputs

Consumed through public contracts and the public synthetic market adapter. No imports of PM3-Strategy Engine internals, PM4, PM5, MT5, or Telegram.

| Input | Owner | Use |
|---|---|---|
| `TradeIntent` | `contracts.v1.strategy` | identity, symbol, `occurred_at`, `idempotency_key`. Direction is **ignored**. |
| Confirmed `OhlcvBar` series | `adapters.market.synthetic` | close-to-close returns; bars with `open_time >= as_of` are forbidden |
| `Pm3ForecastingSection` | `app.settings` | horizon, lookback, min_samples, embargo, timeframe, shadow mode |

`as_of` is `intent.occurred_at` (timezone-aware UTC). Naive datetime is fail-closed (`None`).

Placeholders (read-only, never approval): any future `RiskContext` is **not** a RiskVerdict.

---

## 3. Outputs (enrichment only)

| Artifact | Downstream | Forbidden use |
|---|---|---|
| `ForecastOutput` | future PM4 (read) | not an order; does not mutate intent side |
| `QuantileSet` | inside ForecastOutput | not a direction vote |
| `ModelVersionInfo` | in-memory registry | not PM8 durability |
| Coverage snapshot | health / diagnostics | insufficient data ≠ healthy |

Canonical v1 types stay in `contracts.v1.forecasting`. Sequence 05 extends them backward-compatibly. `TradeIntent` is **not** forked and receives **no** forecast fields. Link is `ForecastOutput.intent_id`.

`requested_volume` on the inbound intent must remain `None`. This module never writes it.

---

## 4. Event flow

```text
TradeIntent (from PM3-Strategy Engine or test helper)
  → feature flag / NullModel short-circuit
  → idempotency cache (same idempotency_key → same ForecastOutput)
  → confirmed bars (synthetic; open_time < as_of; no forming bar)
  → close-to-close returns
  → walk-forward splitter + embargo (>= 1 bar; i+horizon < T)
  → residual quantile envelope (p = 0.05, 0.25, 0.50, 0.75, 0.95)
  → map returns to price: last_confirmed_close * (1 + q)
  → ForecastOutput (producer=pm3_forecasting)
  → in-memory model registry
  → conformal tracker (realize later when horizon bar arrives)
  → in-memory publisher
```

Hard cuts:

```text
PM3 forecasting / QRF  ─X→  PM5 execution
PM3 forecasting / QRF  ─X→  adapters.mt5
PM3 forecasting / QRF  ─X→  Telegram
PM3 forecasting / QRF  ─X→  TradeIntent.direction mutation
ForecastOutput         ─X→  OrderRequest
q50                    ─X→  LONG/SHORT vote
```

Legal future path:

```text
PM2 context → PM3-Strategy Engine TradeIntent
  → PM3 forecasting / QRF ForecastOutput
  → PM4 RiskVerdict ALLOW
  → PM5 Execution
```

---

## 5. Dependency direction

```text
pm3_forecasting
  → contracts.v1 (forecasting, strategy, market, time, identity)
  → adapters.market.synthetic (public confirmed-bar feed)
  → app.capabilities / app.health (manifest + checks only)
  ─X→ modules.pm3_strategy_engine internals
  ─X→ modules.pm4_risk internals
  ─X→ modules.pm5_execution
  ─X→ adapters.mt5
  ─X→ adapters.telegram
  ─X→ sklearn / numpy / pandas / MetaTrader5
```

PM1 `container.py` is the only binder. Flag off → `NullModel`. Flag on (env opt-in in demo/test/research) → `PM3ForecastingModule`.

---

## 6. Contract ownership

| Contract | Owner | Sequence 05 action |
|---|---|---|
| `QuantileSet` / `ForecastOutput` / `ModelVersionInfo` | PM3 forecasting / QRF (v1) | extend, do not fork |
| `TradeIntent` | PM3-Strategy Engine | consume only; do not add forecast fields |
| `OhlcvBar` / `Timeframe` | PM2 / market | consume only |
| `RiskVerdict` | PM4 | do not produce |
| `OrderRequest` | PM5 | do not produce |

`ModelProvider.forecast(intent) -> ForecastOutput | None` stays. Tests may call `forecast_with_bars(intent, bars)`.

---

## 7. Estimator honesty

Sequence 05 ships a **deterministic residual quantile envelope**, not a trained forest:

- Historical horizon-bar simple returns, empirical type-7 percentiles, mapped to price.
- `model_id="residual_quantile_envelope"`, `version="0.1.0"`.
- A later sequence may swap `inference/envelope.py` for a fitted QRF behind the same port. sklearn is not a dependency now.

Side-invariance: BUY and SELL intents with the same bars produce identical `QuantileSet` values. `q50` is the median residual path, not a vote.

---

## 8. Fail-closed behaviours

Return `None` (never raise into execution) when:

- feature flag off (`NullModel` or `feature_enabled=False`);
- missing / blank symbol;
- naive datetime on `as_of` or bars;
- empty / malformed / unordered bars;
- lookahead (`open_time >= as_of` or forming bar);
- insufficient walk-forward samples (`< min_samples`);
- quantile ordering would be violated after mapping.

Idempotency: duplicate `idempotency_key` returns the cached `ForecastOutput` (same `forecast_id`).

---

## 9. Health, registry, conformal

- Module is **non-critical**. Kernel still boots if coverage is thin.
- Conformal tracker is in-memory. Insufficient realized samples ≠ healthy.
- Model registry is in-memory, not PM8. `registry_uri` may be a `memory://` locator.

---

## 10. Feature flag and configuration

| Knob | Value |
|---|---|
| YAML `feature_flags.forecasting` | **false** |
| Env opt-in | `BOTMODULEPROJECT1_FEATURE__ENABLE_FORECASTING=true` |
| Allowed profiles | demo, test, research (catalog unchanged) |
| `horizon_bars` | 4 |
| `lookback_bars` | 64 |
| `min_samples` | 20 |
| `embargo_bars` | 1 |
| `timeframe` | H1 |
| `operating_mode` | shadow |
| `observe_only` | true |

---

## 11. Out of scope (Sequence 05)

- Fitted Quantile Regression Forest / sklearn / numpy / pandas
- Mutating TradeIntent or creating one
- PM4 risk math, ALLOW path, position sizing
- PM5 execution, MT5, Telegram
- Durable model registry (PM8)
- Live / demo / paper / production trading
