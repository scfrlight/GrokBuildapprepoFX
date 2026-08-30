# RB-FAILED-PROJECTION: Failed projection rebuild

Sequence 14 runbook. Observe-only. Not a trading procedure.

1. **Trigger.** projection rebuild throws or lags.
2. **Observable symptoms.**
- projection.lag
- projection_error
3. **Safety classification.** isolated-rebuild
4. **Automatic system behavior.** Do not rebuild on the live write connection if it can race.
5. **Operator inspection commands.**
- python -m botmoduleproject1 observe --profile test --config configs/test.example.yaml --json
6. **Prohibited operator actions.**
- Do not delete the event log to speed rebuild.
- Do not send live, paper, or real Demo orders.
- Do not bind Telegram Bot API.
- Do not bypass PM4.
- Do not treat SIM-* or DEMO-* as broker truth.
- Do not set trading_readiness=true.
- Do not start Sequence 15.
7. **Recovery steps.**
- Rebuild in isolation.
8. **Verification steps.**
- metric catalog includes projection.lag
9. **Rollback steps.**
- Keep previous projection.
10. **Evidence to preserve.**
- rebuild duration sample
11. **Closure criteria.** Projection either rebuilt or explicitly stale.
12. **Escalation criteria.** Rebuild loops.

Executable check id: `metric_catalog`
