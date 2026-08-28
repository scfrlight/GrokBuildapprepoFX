# PM2 — Market Context Engine

Pre-trade intelligence: universe scan, regime, confluence, ranking, suppression,
publication. **Not a trading bot.** No orders, no sizing, no QRF/ML.

Feature flag `enable_pm2_market_data` defaults **false**. YAML must stay false.
Opt-in only in **test** and **research** via
`BOTMODULEPROJECT1_FEATURE__ENABLE_PM2_MARKET_DATA=true`.

Operating mode defaults to `shadow` — handoff eligibility is always false.

HMM/GMM adapters exist as disabled stubs (`infer()` returns `None`).

Synthetic confirmed-bar feed only. Real MT5 is a later sequence.
