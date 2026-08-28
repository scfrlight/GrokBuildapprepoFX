# Python package `botmoduleproject1`

Import root for the trading system.

Sequence 01–02: contracts + PM1 kernel + governance.  
Sequence 03: PM2 market context (flag off).  
Sequence 04: **PM3-Strategy Engine** (flag off; TradeIntent is not an order).  
Sequence 05: **PM3 forecasting / QRF** (flag off; ForecastOutput is not an order).  
Sequence 06: **PM4 Risk Gate** (flag off; ALLOW is not an order; PM5 closed).  
Sequence 07: **PM5 Execution** (flag off; `DisabledExecution`; SIM-* is not broker truth).  
Sequence 08: **PM6 Post-Trade** (flag off; `NullMonitoring`; observe-only).  
Sequence 09: **PM7 Persistence** (flag off; `NullLedger`; append-only; not production durable).

CLI: `python -m botmoduleproject1 --profile test doctor`

Forbidden still: MT5 calls, Telegram, order send, fitted QRF, production distributed DB.  
Not trade-ready. Live trading is disabled. Python 3.11+ required.
