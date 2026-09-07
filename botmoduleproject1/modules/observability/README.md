# Sequence 14 — Observability (+ Seq 15 demo readiness gate)

Package: `botmoduleproject1.modules.observability`

Not PM6. Not an execution engine. Observe-only by default.

- Structured logs: `logging_events.py`
- Metrics catalog: `metrics.py` (bounded labels)
- Health / readiness dimensions: `health_model.py` (not one boolean)
- Demo-only readiness allowlist: `demo_readiness.py` (Sequence 15 Phase 1)
- Error taxonomy: `errors.py` (public-safe messages)
- Runbooks: `runbooks.py` → `docs/runbooks/`
- Redaction: `redaction.py`

`trading_readiness` defaults to `false`. It may become `true` only on the
explicit DEMO allowlist (`enable_demo_trading_readiness` env opt-in + demo
profile + recovery/integrity). LIVE / paper / production stay refused.
Telegram Bot API stays refused. Feature flags stay default-off. Real MT5 is
not wired by this package. PM4 remains the exclusive risk gate.
