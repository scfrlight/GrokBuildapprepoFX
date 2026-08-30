# RB-SECRET-EXPOSURE: Secret exposure response

Sequence 14 runbook. Observe-only. Not a trading procedure.

1. **Trigger.** Secret value found in logs, evidence, or chat.
2. **Observable symptoms.**
- secret_handling_error
3. **Safety classification.** critical
4. **Automatic system behavior.** Redact. Fail export. Halt.
5. **Operator inspection commands.**
- python -m pytest tests/unit/test_seq14_observability.py::test_secret_redaction_in_log_metadata --tb=short
6. **Prohibited operator actions.**
- Do not commit a rotation secret to git.
- Do not send live, paper, or real Demo orders.
- Do not bind Telegram Bot API.
- Do not bypass PM4.
- Do not treat SIM-* or DEMO-* as broker truth.
- Do not set trading_readiness=true.
- Do not start Sequence 15.
7. **Recovery steps.**
- Rotate credential.
- Purge leaked artifact.
- Re-run redaction tests.
8. **Verification steps.**
- redaction tests fail if a known secret is injected
9. **Rollback steps.**
- Revert the leaking commit if already pushed.
10. **Evidence to preserve.**
- redacted copy only
11. **Closure criteria.** No secret value remains in git or evidence.
12. **Escalation criteria.** Always escalate exposures.

Executable check id: `redaction`
