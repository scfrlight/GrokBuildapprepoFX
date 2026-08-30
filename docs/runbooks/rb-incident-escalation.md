# RB-INCIDENT-ESCALATION: Incident escalation

Sequence 14 runbook. Observe-only. Not a trading procedure.

1. **Trigger.** Unresolved incident or integrity/secret event.
2. **Observable symptoms.**
- incidents.unresolved > 0
3. **Safety classification.** escalate
4. **Automatic system behavior.** Do not auto-close. Do not auto-promote.
5. **Operator inspection commands.**
- python -m botmoduleproject1 observe --profile test --config configs/test.example.yaml --json
6. **Prohibited operator actions.**
- Do not close without evidence.
- Do not send live, paper, or real Demo orders.
- Do not bind Telegram Bot API.
- Do not bypass PM4.
- Do not treat SIM-* or DEMO-* as broker truth.
- Do not set trading_readiness=true.
- Do not start Sequence 15.
7. **Recovery steps.**
- Preserve evidence.
- Notify architect.
8. **Verification steps.**
- incident metrics exist
9. **Rollback steps.**
- N/A
10. **Evidence to preserve.**
- incident bundle
11. **Closure criteria.** Escalation recorded.
12. **Escalation criteria.** This runbook IS the escalation.

Executable check id: `metric_catalog`
