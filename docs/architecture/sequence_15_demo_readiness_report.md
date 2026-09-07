# Sequence 15 Phase 1 — Demo-only trading readiness allowlist

Date (UTC): 2026-09-07  
Git home: `scfrlight/GrokBuildapprepoFX`  
Status: Phase 1 implemented (readiness FSM / allowlist only).

## Scope

Unlock Sequence 15 as a **DEMO-ONLY** readiness path:

- `trading_readiness` / `accept_trade` may become true **only** when the explicit DEMO allowlist passes.
- LIVE, paper, and production remain fail-closed.
- Real MT5 venue, Seq 11 container wiring on this host, mobile BFF, and live/production flags-on-by-default are **not** wired.

## Allowlist predicates (all required)

1. Profile `demo` (not live/test/research/backtest)
2. Feature flag `enable_demo_trading_readiness` enabled via **env opt-in** (dangerous; YAML cannot enable)
3. `trading_mode` / CLI mode not `live` or `paper`
4. `app.environment` not production/prod/live
5. `safety.live_trading_enabled` false
6. Recovery complete (lifecycle past WIRED)
7. Not stale data; integrity ok

Implementation: `botmoduleproject1/modules/observability/demo_readiness.py`  
Consumed by: `health_model.evaluate`.

## Safety locks retained

- PM4 remains the exclusive risk gate
- Live CLI / profile / trading_mode still raise `LiveTradingDisabledError`
- Telegram Bot API refused
- Feature flags YAML default false
- Broker venue remains UNAVAILABLE without an MT5 adapter flag (real terminal still absent)

## Tests

`tests/unit/test_seq15_demo_readiness.py`

## Residual risks

- Readiness open ≠ order send (PM4/PM5/execution flags still gate actual paths)
- No real MT5 on Linux CI host
- Operators must not confuse DEMO allowlist with live enablement
