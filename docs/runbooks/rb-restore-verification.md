# RB-RESTORE-VERIFICATION: Restore verification

Sequence 14 runbook. Observe-only. Not a trading procedure.

1. **Trigger.** Operator asks to restore a backup file.
2. **Observable symptoms.**
- verify_file ok or MigrationError
3. **Safety classification.** halt-on-mismatch
4. **Automatic system behavior.** Mismatch raises. Live sequence not mutated.
5. **Operator inspection commands.**
- python scripts/bot/emit_evidence.py --out-dir docs/evidence
6. **Prohibited operator actions.**
- Do not --force a checksum skip.
- Do not send live, paper, or real Demo orders.
- Do not bind Telegram Bot API.
- Do not bypass PM4.
- Do not treat SIM-* or DEMO-* as broker truth.
- Do not set trading_readiness=true.
- Do not start Sequence 15.
7. **Recovery steps.**
- Use a verified file only.
8. **Verification steps.**
- sequence_before == sequence_after_verify
9. **Rollback steps.**
- Keep live db; do not apply the bad dump.
10. **Evidence to preserve.**
- restore_verifications row
11. **Closure criteria.** Verified file or refused restore.
12. **Escalation criteria.** Live seq changed during verify.

Executable check id: `backup_restore`
