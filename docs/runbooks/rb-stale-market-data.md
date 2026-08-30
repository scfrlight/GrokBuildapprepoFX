# RB-STALE-MARKET-DATA: Stale market data

Sequence 14 runbook. Observe-only. Not a trading procedure.

1. **Trigger.** Stale detector fires or last tick age exceeds threshold.
2. **Observable symptoms.**
- botmodule.market.stale_events increments
- operational_health=degraded
3. **Safety classification.** safe-stop
4. **Automatic system behavior.** Routing halted. trading_readiness remains false. Observe-only.
5. **Operator inspection commands.**
- python -m botmoduleproject1 observe --profile test --config configs/test.example.yaml --json
6. **Prohibited operator actions.**
- Do not force a tick.
- Do not widen staleness to keep trading.
- Do not send live, paper, or real Demo orders.
- Do not bind Telegram Bot API.
- Do not bypass PM4.
- Do not treat SIM-* or DEMO-* as broker truth.
- Do not set trading_readiness=true.
- Do not start Sequence 15.
7. **Recovery steps.**
- Wait for fresh data.
- Keep flags off.
8. **Verification steps.**
- stale_data=true implies accept_trade=false
9. **Rollback steps.**
- N/A — safe-stop is the recovery.
10. **Evidence to preserve.**
- observability snapshot
11. **Closure criteria.** Stale flag cleared; still not trade-ready.
12. **Escalation criteria.** Stale persists across sessions.

Executable check id: `stale_forces_safe_stop`
