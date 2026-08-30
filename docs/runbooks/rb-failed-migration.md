# RB-FAILED-MIGRATION: Failed migration

Sequence 14 runbook. Observe-only. Not a trading procedure.

1. **Trigger.** upgrade_to/rollback raises MigrationError.
2. **Observable symptoms.**
- schema version unchanged
3. **Safety classification.** halt
4. **Automatic system behavior.** Refuse v1 drop with a non-empty journal.
5. **Operator inspection commands.**
- python -m pytest tests/unit/test_pm8a_seq10.py --tb=short
6. **Prohibited operator actions.**
- Do not DROP tables by hand.
- Do not send live, paper, or real Demo orders.
- Do not bind Telegram Bot API.
- Do not bypass PM4.
- Do not treat SIM-* or DEMO-* as broker truth.
- Do not set trading_readiness=true.
- Do not start Sequence 15.
7. **Recovery steps.**
- Stay on current version.
- Inspect MigrationError.
8. **Verification steps.**
- tests refuse v1 drop
9. **Rollback steps.**
- rollback only 2→1 when allowed
10. **Evidence to preserve.**
- migration log
11. **Closure criteria.** Schema consistent; journal intact.
12. **Escalation criteria.** Partial DDL applied.

Executable check id: `migration_refuse_v1`
