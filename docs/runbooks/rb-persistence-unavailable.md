# RB-PERSISTENCE-UNAVAILABLE: Persistence unavailable

Sequence 14 runbook. Observe-only. Not a trading procedure.

1. **Trigger.** SQLite/API errors or NullStorage when writes are required.
2. **Observable symptoms.**
- persistence_readiness fail/degraded
- persistence.errors
3. **Safety classification.** halt-writes
4. **Automatic system behavior.** Refuse unjournaled writes. Not-ready for trade.
5. **Operator inspection commands.**
- python -m botmoduleproject1 observe --profile test --config configs/test.example.yaml --json
6. **Prohibited operator actions.**
- Do not switch to an unversioned file drop.
- Do not send live, paper, or real Demo orders.
- Do not bind Telegram Bot API.
- Do not bypass PM4.
- Do not treat SIM-* or DEMO-* as broker truth.
- Do not set trading_readiness=true.
- Do not start Sequence 15.
7. **Recovery steps.**
- Inspect store path.
- Follow backup/restore if corruption.
8. **Verification steps.**
- persistence dimension not PASS while flag off is expected DEGRADED
9. **Rollback steps.**
- Remain on NullStorage.
10. **Evidence to preserve.**
- persistence error logs
11. **Closure criteria.** Writes either journaled or refused.
12. **Escalation criteria.** Integrity also failing.

Executable check id: `persistence_dimension`
