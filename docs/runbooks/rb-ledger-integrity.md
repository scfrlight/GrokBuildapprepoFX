# RB-LEDGER-INTEGRITY: Ledger integrity mismatch

Sequence 14 runbook. Observe-only. Not a trading procedure.

1. **Trigger.** Hash chain or checksum mismatch.
2. **Observable symptoms.**
- integrity_error
- ledger_compromised
3. **Safety classification.** halt
4. **Automatic system behavior.** No rewrite. Correction event only. trading halted.
5. **Operator inspection commands.**
- python scripts/bot/emit_evidence.py --out-dir docs/evidence
6. **Prohibited operator actions.**
- Do not delete audit rows.
- Do not rehash the chain.
- Do not send live, paper, or real Demo orders.
- Do not bind Telegram Bot API.
- Do not bypass PM4.
- Do not treat SIM-* or DEMO-* as broker truth.
- Do not set trading_readiness=true.
- Do not start Sequence 15.
7. **Recovery steps.**
- Preserve files.
- Escalate.
- Use correction events.
8. **Verification steps.**
- committed rows unchanged
9. **Rollback steps.**
- Restore from verified backup only after checksum match.
10. **Evidence to preserve.**
- ledger dump
- backup checksum
11. **Closure criteria.** Mismatch documented; chain not rewritten.
12. **Escalation criteria.** Always escalate integrity failures.

Executable check id: `integrity_fail_not_ready`
