# Health / readiness guide

Do not collapse these into one boolean.

| Dimension | Meaning | Seq 14 default (flags off, no venue) |
|---|---|---|
| liveness | Process assembled | pass |
| readiness | May accept observe/doctor | pass (if not FAILED) |
| operational_health | Kernel diagnostic | degraded |
| trading_readiness | May send orders | **fail (always)** |
| recovery_readiness | Recovery finished | degraded until lifecycle past WIRED |
| persistence_readiness | Journal usable | degraded on NullStorage; fail on integrity error |
| broker_venue | MT5 present | **unavailable** — not pass |
| operator_readiness | Operator plane | degraded (Telegram refused, NullOperator) |

Alive  confuses with ready. Ready for observe is not ready to trade. Missing venue is unavailable, never pass. Stale data is safe-stop. Recovery incomplete keeps trading_readiness false. All flags off keeps trading_readiness false. Live profile is fail-closed at bootstrap.

Transitions: `TRANSITION_TABLE` in `health_model.py`, tested in `test_transition_table_covers_critical_rows`.
