# RB-OUTBOX-BACKLOG: Outbox backlog

Sequence 14 runbook. Observe-only. Not a trading procedure.

1. **Trigger.** outbox.backlog gauge above threshold.
2. **Observable symptoms.**
- relay lag growing
3. **Safety classification.** degraded
4. **Automatic system behavior.** Do not drop. Do not send to a real venue.
5. **Operator inspection commands.**
- python -m botmoduleproject1 observe --profile test --config configs/test.example.yaml --json
6. **Prohibited operator actions.**
- Do not purge the outbox to look green.
- Do not send live, paper, or real Demo orders.
- Do not bind Telegram Bot API.
- Do not bypass PM4.
- Do not treat SIM-* or DEMO-* as broker truth.
- Do not set trading_readiness=true.
- Do not start Sequence 15.
7. **Recovery steps.**
- Inspect consumers.
- Keep flags off.
8. **Verification steps.**
- backlog metric exists in catalog
9. **Rollback steps.**
- N/A
10. **Evidence to preserve.**
- outbox snapshot
11. **Closure criteria.** Backlog explained; no venue send.
12. **Escalation criteria.** Dead-letter also growing.

Executable check id: `metric_catalog`
