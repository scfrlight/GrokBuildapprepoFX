# RB-BACKUP-VERIFICATION: Backup verification

Sequence 14 runbook. Observe-only. Not a trading procedure.

1. **Trigger.** Scheduled or manual backup().
2. **Observable symptoms.**
- backup_restore.log verified=True
3. **Safety classification.** observe
4. **Automatic system behavior.** Checksum is dump-specific (UUIDs/timestamps). Restore verifies against THAT dump.
5. **Operator inspection commands.**
- python scripts/bot/emit_evidence.py --out-dir docs/evidence
6. **Prohibited operator actions.**
- Do not expect local and CI dump checksums to match.
- Do not send live, paper, or real Demo orders.
- Do not bind Telegram Bot API.
- Do not bypass PM4.
- Do not treat SIM-* or DEMO-* as broker truth.
- Do not set trading_readiness=true.
- Do not start Sequence 15.
7. **Recovery steps.**
- If verified=False, refuse restore.
8. **Verification steps.**
- runtime_untouched=True
- payload_canonical comparable
9. **Rollback steps.**
- Discard the bad file.
10. **Evidence to preserve.**
- backup_restore.log
- dump checksum
- payload_canonical_sha256
11. **Closure criteria.** File hashes to its own checksum.
12. **Escalation criteria.** Checksum mismatch on the same file.

Executable check id: `backup_restore`
