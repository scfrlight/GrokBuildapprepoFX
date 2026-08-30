# RB-CORRUPTED-EVIDENCE: Corrupted evidence package

Sequence 14 runbook. Observe-only. Not a trading procedure.

1. **Trigger.** Evidence checksum mismatch or secret in bundle.
2. **Observable symptoms.**
- verified=False
- redaction failure
3. **Safety classification.** reject
4. **Automatic system behavior.** Refuse the package. Do not fake a green checksum.
5. **Operator inspection commands.**
- python scripts/bot/emit_seq14_evidence.py --out-dir docs/evidence/seq14
6. **Prohibited operator actions.**
- Do not recompute a matching checksum over mutated bytes.
- Do not send live, paper, or real Demo orders.
- Do not bind Telegram Bot API.
- Do not bypass PM4.
- Do not treat SIM-* or DEMO-* as broker truth.
- Do not set trading_readiness=true.
- Do not start Sequence 15.
7. **Recovery steps.**
- Regenerate from a clean run.
8. **Verification steps.**
- payload_canonical vs dump checksum distinction documented
9. **Rollback steps.**
- Keep the corrupt file as evidence of corruption, isolated.
10. **Evidence to preserve.**
- bad checksum
- new clean bundle
11. **Closure criteria.** Only clean bundles are linked from the audit.
12. **Escalation criteria.** Someone asks to 'just hash it again'.

Executable check id: `evidence_no_secrets`
