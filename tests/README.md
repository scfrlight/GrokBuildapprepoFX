- `unit/` — isolated + PM2 + PM3-Strategy Engine + PM3 forecasting / QRF + PM4 Risk Gate + PM5 Execution + PM6 Post-Trade
- `contract/` — schema and layer rules
- `integration/` — fakes, never live broker by default
- `e2e/` — future doctor/demo-observe paths

Sequence 08: PM6 post-trade / surveillance / incident tests added. ADR-008: sandbox pytest on CPython 3.10.21; production floor remains 3.11+.
