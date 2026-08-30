# RB-SIM-EXEC-REJECTION: Simulated execution rejection

Sequence 14 runbook. Observe-only. Not a trading procedure.

1. **Trigger.** SIM/DEMO engine rejects an intent.
2. **Observable symptoms.**
- broker_rejected public message
3. **Safety classification.** simulation
4. **Automatic system behavior.** Record rejection. Do not invent a fill.
5. **Operator inspection commands.**
- python -m pytest tests/unit/test_seq11_mt5_exit.py --tb=short
6. **Prohibited operator actions.**
- Do not coerce SIM/DEMO to a venue ticket.
- Do not send live, paper, or real Demo orders.
- Do not bind Telegram Bot API.
- Do not bypass PM4.
- Do not treat SIM-* or DEMO-* as broker truth.
- Do not set trading_readiness=true.
- Do not start Sequence 15.
7. **Recovery steps.**
- Inspect PM4 verdict and simulation reason.
8. **Verification steps.**
- SIM-* / DEMO-* never broker truth tests green
9. **Rollback steps.**
- N/A
10. **Evidence to preserve.**
- simulation receipt
11. **Closure criteria.** Rejection recorded; no broker send.
12. **Escalation criteria.** A fill appears without a venue.

Executable check id: `sim_not_broker_truth`
