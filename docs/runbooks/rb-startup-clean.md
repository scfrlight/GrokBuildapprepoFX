# RB-STARTUP-CLEAN: Clean startup

Sequence 14 runbook. Observe-only. Not a trading procedure.

1. **Trigger.** Operator starts doctor/test/observe on Python 3.11+ with default flags.
2. **Observable symptoms.**
- process banners NOT TRADE READY
- lifecycle degraded or ready-for-observe
3. **Safety classification.** observe-only
4. **Automatic system behavior.** Version guard, load settings, Null* binds, health probes, trading_readiness=false.
5. **Operator inspection commands.**
- python -m botmoduleproject1 doctor --profile test --config configs/test.example.yaml
6. **Prohibited operator actions.**
- Do not pass --profile live.
- Do not send live, paper, or real Demo orders.
- Do not bind Telegram Bot API.
- Do not bypass PM4.
- Do not treat SIM-* or DEMO-* as broker truth.
- Do not set trading_readiness=true.
- Do not start Sequence 15.
7. **Recovery steps.**
- Fix Python/config if doctor exits non-zero.
8. **Verification steps.**
- doctor exits 0
- banner contains NOT TRADE READY
9. **Rollback steps.**
- Stop the process. No state to roll back.
10. **Evidence to preserve.**
- doctor.out
- config fingerprint
11. **Closure criteria.** Kernel assembled; live closed.
12. **Escalation criteria.** Startup fails after config is valid.

Executable check id: `doctor_exits_zero`
