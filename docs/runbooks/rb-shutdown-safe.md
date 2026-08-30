# RB-SHUTDOWN-SAFE: Safe shutdown

Sequence 14 runbook. Observe-only. Not a trading procedure.

1. **Trigger.** Operator stops the process or runtime.stop() is called.
2. **Observable symptoms.**
- lifecycle STOPPING then STOPPED
3. **Safety classification.** observe-only
4. **Automatic system behavior.** No orders are flushed. Outbox is not force-drained onto a venue.
5. **Operator inspection commands.**
- python -m botmoduleproject1 doctor --profile test --config configs/test.example.yaml
6. **Prohibited operator actions.**
- Do not SIGKILL to skip audit.
- Do not send live, paper, or real Demo orders.
- Do not bind Telegram Bot API.
- Do not bypass PM4.
- Do not treat SIM-* or DEMO-* as broker truth.
- Do not set trading_readiness=true.
- Do not start Sequence 15.
7. **Recovery steps.**
- Allow STOPPING→STOPPED.
- Restart with doctor.
8. **Verification steps.**
- no broker send on shutdown
9. **Rollback steps.**
- N/A
10. **Evidence to preserve.**
- runtime log
11. **Closure criteria.** Process stopped; no live side effects.
12. **Escalation criteria.** Process hangs in STOPPING.

Executable check id: `runtime_stop`
