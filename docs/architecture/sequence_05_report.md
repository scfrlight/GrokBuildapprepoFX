# Sequence 05 Report — PM3 forecasting / QRF

Date (UTC): 2026-08-28  
Git home: `scfrlight/GrokBuildapprepoFX`  
Display name: **PM3 forecasting / QRF** (never shortened to “PM3”)

## 1. Git commit hash

Kernel not yet committed (parent will push). Sequence 04 parent on GitHub is `8619730`. This workspace has no `.git`; the Sequence 05 kernel is complete in `/workspace` and ready for the parent process to commit.

## 2. Created / updated files

### Created (PM3 forecasting / QRF kernel)

- `botmoduleproject1/modules/pm3_forecasting/` (config, domain, features, research, inference, registry, application, diagnostics, publication, module, capabilities, contracts)
- `configs/pm3_forecasting.example.yaml`
- `docs/architecture/pm3_forecasting_integration_plan.md`
- `docs/adr/ADR-010-pm3-forecasting-research-kernel.md`
- `docs/prompts/PM3_Forecasting_Sequence05_Prompt.md`
- `tests/unit/pm3fx_support.py`
- `tests/unit/test_pm3_fx_*.py`
- `tests/contract/test_pm3_forecast_contracts.py`

### Updated

- `botmoduleproject1/contracts/v1/forecasting.py` (QuantileSet non-decreasing validator; ForecastOutput coverage / sample_size / horizon_seconds / diagnostics)
- `botmoduleproject1/app/feature_flags.py` (catalog description)
- `botmoduleproject1/app/settings.py` (`Pm3ForecastingSection`)
- `botmoduleproject1/app/container.py` (`_forecasting_module`)
- `botmoduleproject1/app/README.md`, `botmoduleproject1/README.md`, `botmoduleproject1/__init__.py`
- `configs/base.example.yaml`
- README files, ADR index, architecture baseline, dependency graph, repository assessment, pyproject.toml, tests/README.md

## 3. Pre-implementation integration-plan status

`docs/architecture/pm3_forecasting_integration_plan.md` written before module implementation. ADR-010 accepted.

Plan covers: TradeIntent as read-only input, ForecastOutput as enrichment, forbidden PM5/MT5/Telegram/side-mutation edges, residual quantile envelope honesty, fail-closed behaviours, in-memory registry.

## 4. PM3 forecasting / QRF component status

| Component | Status | Notes |
|---|---|---|
| QuantileSet ordering validator | COMPLETE | non-decreasing; equals allowed |
| ForecastOutput enrichment fields | COMPLETE | coverage, sample_size, horizon_seconds, diagnostics |
| Residual quantile envelope | COMPLETE | Hyndman-Fan type 7; not a fitted QRF |
| Walk-forward + embargo splitter | COMPLETE | `i+horizon < T`; embargo >= 1 bar |
| Confirmed-bar returns | COMPLETE | no lookahead; no forming bar |
| Side-invariance | COMPLETE | BUY/SELL identical quantiles |
| Idempotency cache | COMPLETE | same `idempotency_key` → same `forecast_id` |
| Fail-closed `None` | COMPLETE | flag off, short history, lookahead, malformed, blank symbol |
| Conformal coverage tracker | COMPLETE | in-memory; insufficient data ≠ healthy |
| In-memory model registry | COMPLETE | not PM8; `memory://` URI |
| PM1 registry integration | COMPLETE | `ModelProvider`; NullModel when flag off |
| Configuration | COMPLETE | pydantic schema; YAML knobs; flag false |
| Feature flag | COMPLETE | YAML false; demo/test/research env opt-in |
| Diagnostics | COMPLETE | non-critical health/readiness |
| Tests | COMPLETE | 189 collected / 189 passed |
| Documentation | COMPLETE | plan, ADR-010, persisted prompt, this report |

In-memory registry and conformal tracker are Sequence 05 limitations, not PM8.

## 5. Why ForecastOutput is not an order and does not mutate side

Created: analytical `ForecastOutput` (price-space quantile envelope, model version, identity fields) linked by `intent_id`.

Why not an order: no `OrderRequest`; no lot size; inbound `TradeIntent.requested_volume` stays `None`; no broker send; no PM5/MT5/Telegram import.

Why not a side vote: the envelope ignores `intent.direction`. LONG and SHORT intents with the same bars produce identical quantiles. `q50` is the median residual path, not GO_LONG / GO_SHORT.

Downstream still required: Sequence 06 PM4 `RiskVerdict.status == ALLOW` → PM5 execution.

## 6. Estimator

- Active: residual quantile envelope `0.1.0` over confirmed H1 synthetic bars (lookback 64, horizon 4, embargo 1, min_samples 20).
- Out of scope: fitted sklearn Quantile Regression Forest.
- Percentile method: linear interpolation (Hyndman-Fan type 7). Prices quantized to 5 decimal places.

## 7. Safety controls

- No execution, no risk math, no MT5, no Telegram.
- Feature flag default false; YAML stays false.
- Lookahead / forming bar / unordered bars / insufficient samples → `None`.
- Duplicate `idempotency_key` does not emit a second `forecast_id`.
- Module is non-critical; conformal under-sample is not healthy and is not a kernel halt.

## 8. Test results

- Collected / passed: **189 / 189**
- Prior Sequences 00–04: 159
- Sequence 05 added: 30
- Sandbox runtime: CPython 3.10.21 with ADR-008 interpreter_version patch
- Project floor remains Python 3.11+; a full compliance-run on 3.11 is required outside this sandbox

| File | Tests |
|---|---|
| `tests/contract/test_pm3_forecast_contracts.py` | 5 |
| `tests/unit/test_pm3_fx_no_lookahead.py` | 5 |
| `tests/unit/test_pm3_fx_side_invariance.py` | 2 |
| `tests/unit/test_pm3_fx_envelope.py` | 5 |
| `tests/unit/test_pm3_fx_idempotency.py` | 2 |
| `tests/unit/test_pm3_fx_flag.py` | 5 |
| `tests/unit/test_pm3_fx_safety.py` | 3 |
| `tests/unit/test_pm3_fx_integration.py` | 3 |
| prior Sequences 00–04 | 159 |
| **total** | **189** |

## 9. Known risks and limitations

- Synthetic confirmed bars are not a broker.
- Estimator is a residual quantile envelope, **not** a fitted QRF.
- No real PM4 risk gate (`NullRiskGate` always DENY).
- No PM5 execution (`DisabledExecution` raises).
- No PM7/PM8 durable persistence (in-memory registry and conformal tracker only).
- No real MT5.
- Runtime still boots DEGRADED because the critical risk contributor fails closed.
- Feature flag must stay false in YAML.

## 10. Build gate

**PASS**

## 11. Trading readiness

The system is NOT ready for live trading, demo trading, paper trading, or production.

## 12. Next step

Sequence 06 — PM4 Risk Gate.
