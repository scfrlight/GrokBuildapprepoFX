# Named projections

Read models, not canonical truth. Built only from the event/ledger stream.

Names: open_orders, open_positions, closed_trades, symbol_performance, profile_performance, daily_summary, operator_dashboard, reconciliation_alerts, strategy_memory, anomaly_summary.

- Rebuild wipes rows and replays sequence order.
- Duplicate delivery is ignored via `processed_events`.
- Lag = ledger tip − projection last_event_seq.
- Direct business writes to projection tables are not part of the public API.

Source: **RECONSTRUCTED-SOURCE** (PM8a named set).
