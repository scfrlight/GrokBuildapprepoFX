# ADR-007: Risk-gate exclusivity before execution

- Status: Accepted
- Date: 2026-08-28
- Sequence: 00

## Context

Legacy auto-exec combined filters, ML probability, duplicate window, and `--execute` inside the scanner. There was no exclusive risk module that PM5 was forced to consult. Institutional policy: no order without a positive risk verdict.

## Decision

- PM4 is the **only** final permission issuer for execution.
- PM5 accepts an `OrderCommand` only if it references a `RiskVerdict` with `status=ALLOW` for the same `intent_id` / `idempotency_key`, not expired.
- Strategy, forecast, operator "approve" buttons, and Telegram commands cannot bind orders.
- An operator force-approve (if ever built) still produces a *new* intent that must pass PM4.
- If PM4 is unimplemented, missing, or uncertain, the verdict is DENY / HALT — fail closed.
- Kill-switch and drawdown governor live in PM4, not in the broker adapter.

## Consequences

- Sequence 00 does not implement PM4, but contracts in Sequence 01 must include `RiskVerdict`.
- Tests in later sequences must attempt to send an order without a verdict and expect refusal.
- PM3-Strategy Engine is structurally unable to call PM5.

## Alternatives considered

1. Keep filters inside the scanner — rejected.
2. Dual gates (PM4 and PM5 duplicate checks) as *both* sufficient — rejected; PM5 checks presence of PM4 verdict, it does not replace PM4.
3. Operator override that skips PM4 — rejected.

## Validation implications

- Contract: `OrderCommand` includes `risk_verdict_id` (required).
- Integration (future): mutating a verdict after ALLOW cannot be reused.
- Import linter: `pm5_execution` must not import `pm3_strategy_engine`.
