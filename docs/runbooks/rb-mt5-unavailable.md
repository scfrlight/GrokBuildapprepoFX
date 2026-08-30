# RB-MT5-UNAVAILABLE: MT5 unavailable

Sequence 14 runbook. Observe-only. Not a trading procedure.

1. **Trigger.** No terminal, flag off, or adapter refused.
2. **Observable symptoms.**
- broker_venue=unavailable
3. **Safety classification.** unavailable-not-pass
4. **Automatic system behavior.** No real send. DEMO-* is not broker truth.
5. **Operator inspection commands.**
- python -m botmoduleproject1 observe --profile test --config configs/test.example.yaml --json
6. **Prohibited operator actions.**
- Do not attach a real MT5 terminal.
- Do not enable mt5_demo_adapter in YAML.
- Do not send live, paper, or real Demo orders.
- Do not bind Telegram Bot API.
- Do not bypass PM4.
- Do not treat SIM-* or DEMO-* as broker truth.
- Do not set trading_readiness=true.
- Do not start Sequence 15.
7. **Recovery steps.**
- Leave venue unavailable.
8. **Verification steps.**
- venue_present=false
- accept_trade=false
9. **Rollback steps.**
- N/A
10. **Evidence to preserve.**
- observability snapshot
11. **Closure criteria.** Venue unavailable documented.
12. **Escalation criteria.** Any attempt to open a live socket.

Executable check id: `venue_absent_not_pass`
