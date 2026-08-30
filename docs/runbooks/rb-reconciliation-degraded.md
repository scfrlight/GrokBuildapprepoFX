# RB-RECONCILIATION-DEGRADED: Reconciliation degraded

Sequence 14 runbook. Observe-only. Not a trading procedure.

1. **Trigger.** No venue, or mismatch vs SIM/DEMO tickets.
2. **Observable symptoms.**
- reconciliation.degraded_count
- broker_venue=unavailable
3. **Safety classification.** degraded-not-pass
4. **Automatic system behavior.** Status=degraded. Absence of venue never pass.
5. **Operator inspection commands.**
- python -m botmoduleproject1 observe --profile test --config configs/test.example.yaml --json
6. **Prohibited operator actions.**
- Do not force reconciliation=pass.
- Do not send live, paper, or real Demo orders.
- Do not bind Telegram Bot API.
- Do not bypass PM4.
- Do not treat SIM-* or DEMO-* as broker truth.
- Do not set trading_readiness=true.
- Do not start Sequence 15.
7. **Recovery steps.**
- Leave degraded.
- Do not attach a real terminal.
8. **Verification steps.**
- broker_venue is unavailable when flags off
9. **Rollback steps.**
- N/A
10. **Evidence to preserve.**
- reconciliation record
11. **Closure criteria.** Status is degraded or unavailable, never silent pass.
12. **Escalation criteria.** Mismatch against an expected simulation.

Executable check id: `venue_absent_not_pass`
