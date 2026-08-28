# Runtime Modes and Safety Policy

Status: Accepted for Sequence 00  
Date (UTC): 2026-08-28

## 1. Mode catalog

| Mode | CLI token | May send broker orders | Default | Purpose |
|---|---|---|---|---|
| `test` | `test` | No | Allowed | Deterministic unit/contract tests |
| `doctor` | `doctor` | No | Allowed | Config, import, and adapter preflight diagnostics |
| `backtest` | `backtest` | No | Allowed (future) | Historical simulation against recorded data |
| `research` | `research` | No | Allowed (future) | Offline notebooks / PM9a studio |
| `demo` | `demo` | **Not until preflight + recovery + risk readiness** | Default trading-mode *label* | MT5 Demo only, still gated |
| `paper` / `dry-run` | `paper`, `dry-run` | No | Allowed | Intent + risk path without broker send |
| `observe-only` | `observe-only` | No | Safe fallback | Ingest and record, never act |
| `live-disabled` | `live-disabled` | No | Compile-time/config default | Explicit non-live posture |
| `live` | `live` | **Rejected** | Disabled | Recognized so operators get a clear error |

`TRADING_MODE=demo` and `LIVE_TRADING_ENABLED=false` are the committed defaults.

## 2. Live mode policy

- The CLI and config parser **must recognize** `live` so a mis-typed config is not silently coerced to demo.
- Recognition is not permission. `live` exits with a **safe error** before composition root constructs a broker session.
- Enabling live trading in the future requires a dedicated evidentiary ADR, dual control, and code change. It is out of scope for Sequences 00–01.

Suggested error (to be implemented in PM1, not now):

```text
LIVE TRADING IS DISABLED.
Refusing to start because TRADING_MODE=live or LIVE_TRADING_ENABLED=true.
This build is demo-first. See docs/architecture/runtime_modes.md and ADR-002.
```

## 3. Demo mode is not a free pass

Demo must not send orders until **all** of the following are true (future PM1/PM4/PM5/PM8):

1. Preflight / `doctor` checks passed.
2. Readiness: market data, clock, persistence, and risk module reported ready.
3. Recovery completed and ledger consistent.
4. Risk engine produced a process-level `RiskReady` (not implemented in Sequence 00).
5. `LIVE_TRADING_ENABLED=false` still holds.
6. Broker account type is Demo.

Until those exist, demo is a **label** and the host must behave as observe-only.

## 4. Failure behaviour

| Condition | Behaviour | Mode after |
|---|---|---|
| Unknown / invalid config | Stop | process exit ≠ 0 |
| Secret missing for an enabled adapter | Stop (do not start half-wired) | exit ≠ 0 |
| Stale market data | Degrade | `observe-only` |
| Broker connection loss | Degrade, cancel new intents | `observe-only` |
| Incomplete recovery | Stop / halt | no orders |
| Ledger inconsistency | Halt | `observe-only` or exit |
| Risk engine unavailable | Fail closed | no orders |
| Telegram down | Degraded ops | trading unchanged (still gated) |
| Model registry empty | Degraded forecast | risk fail-closed if forecast required |

Safe behaviours are only: **stop**, **degraded**, **observe-only**. There is no "best-effort send".

## 5. Startup / readiness / liveness dependencies

| Probe | Required (future) | Sequence 00 |
|---|---|---|
| Startup | Valid config, UTC clock, `LIVE_TRADING_ENABLED=false`, mode ≠ live | Docs + templates only |
| Readiness | Persistence recoverable, risk ready, data not stale | Not implemented |
| Liveness | Host event loop heartbeat | Not implemented |

Critical for startup: configuration, clock, mode guard.  
Critical for readiness: persistence recovery, risk, market data.  
Critical for liveness: runtime heartbeat. Telegram is never a liveness dependency.

## 6. Feature flags

All future capabilities default to **disabled**:

```text
FEATURE_STRATEGY_ENGINE=false
FEATURE_FORECASTING=false
FEATURE_RISK_ENGINE=false
FEATURE_EXECUTION=false
FEATURE_TELEGRAM=false
FEATURE_FINE_TUNE_STUDIO=false
```

A flag cannot override `LIVE_TRADING_ENABLED=false`.
