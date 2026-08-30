# RB-RECOVERY-AFTER-RESTART: Recovery after restart

Sequence 14 runbook. Observe-only. Not a trading procedure.

1. **Trigger.** Process restart. RestartDrill or orchestrator recovery.
2. **Observable symptoms.**
- reopen seq unchanged
- recovery_readiness
3. **Safety classification.** recover-then-observe
4. **Automatic system behavior.** Recovery before routing. trading_readiness=false.
5. **Operator inspection commands.**
- python scripts/bot/emit_evidence.py --out-dir docs/evidence
6. **Prohibited operator actions.**
- Do not route before recovery completes.
- Do not send live, paper, or real Demo orders.
- Do not bind Telegram Bot API.
- Do not bypass PM4.
- Do not treat SIM-* or DEMO-* as broker truth.
- Do not set trading_readiness=true.
- Do not start Sequence 15.
7. **Recovery steps.**
- Run RestartDrill.
- Confirm sequence.
8. **Verification steps.**
- restart_drill.log passed=True
9. **Rollback steps.**
- Stop if integrity invalid.
10. **Evidence to preserve.**
- restart_drill.log
11. **Closure criteria.** Reopen integrity valid; still not trade-ready.
12. **Escalation criteria.** Sequence moved or integrity invalid.

Executable check id: `restart_drill`
