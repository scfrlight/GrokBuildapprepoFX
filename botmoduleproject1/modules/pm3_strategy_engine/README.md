# PM3-Strategy Engine

Full name is **PM3-Strategy Engine**. Do not shorten to “PM3” in code or docs.

Produces `TradeIntent` or `NoTradeDecision` from public PM2 context. Must not call execution, risk, MT5, or Telegram. Feature flag `enable_pm3_strategy_engine` stays false in YAML.
