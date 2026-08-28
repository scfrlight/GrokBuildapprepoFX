# ADR-002: Demo-first and live-disabled safety policy

- Status: Accepted
- Date: 2026-08-28
- Sequence: 00

## Context

The product target is MT5 Demo for EURUSD. Legacy V7 can auto-send orders when `execution_mode=auto` and `--execute` are combined. Live trading in this codebase would be an unacceptable default.

## Decision

- Default `TRADING_MODE=demo`.
- Default `LIVE_TRADING_ENABLED=false`.
- `live` is a recognized mode that **fails closed** at startup.
- Demo order sending is still forbidden until preflight, readiness, recovery, and risk readiness exist.
- Safe responses to uncertainty: stop, degraded, observe-only.

## Consequences

- Operators cannot accidentally enable live via a boolean they do not understand; live requires a future ADR.
- Demo is a broker *venue*, not a permission to trade.
- Feature flags cannot override the live disable.

## Alternatives considered

1. Silent coerce `live` → `demo` — rejected (hides operator intent).
2. Allow demo orders immediately — rejected (no recovery/risk yet).
3. Paper as the only mode until PM5 — acceptable subset; demo remains the default *label*.

## Validation implications

- Config tests: missing live flag equals false.
- CLI tests (PM1): `--mode live` exits non-zero without adapter construction.
- No test may call a real broker.
