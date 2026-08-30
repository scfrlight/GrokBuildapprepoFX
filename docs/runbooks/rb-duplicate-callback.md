# RB-DUPLICATE-CALLBACK: Duplicate callback

Sequence 14 runbook. Observe-only. Not a trading procedure.

1. **Trigger.** Same event_id or execution idempotency key replayed.
2. **Observable symptoms.**
- duplicate_event or duplicate_execution
3. **Safety classification.** safe-ignore
4. **Automatic system behavior.** First commit wins. Second ignored.
5. **Operator inspection commands.**
- python -m botmoduleproject1 observe --profile test --config configs/test.example.yaml --json
6. **Prohibited operator actions.**
- Do not mint a new id to force a second apply.
- Do not send live, paper, or real Demo orders.
- Do not bind Telegram Bot API.
- Do not bypass PM4.
- Do not treat SIM-* or DEMO-* as broker truth.
- Do not set trading_readiness=true.
- Do not start Sequence 15.
7. **Recovery steps.**
- Confirm original record.
8. **Verification steps.**
- idempotency tests remain green
9. **Rollback steps.**
- N/A
10. **Evidence to preserve.**
- idempotency key
- first record id
11. **Closure criteria.** Single committed effect.
12. **Escalation criteria.** Two distinct commits for one key.

Executable check id: `duplicate_ignored`
