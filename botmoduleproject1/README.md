# Python package `botmoduleproject1`

Import root for the trading system.

Sequence 01–02: contracts + PM1 kernel + governance.  
Sequence 03: PM2 market context (flag off).  
Sequence 04: **PM3-Strategy Engine** (flag off; TradeIntent is not an order).  
Sequence 05: **PM3 forecasting / QRF** (flag off; ForecastOutput is not an order).

CLI: `python -m botmoduleproject1 --profile test doctor`

Forbidden still: MT5 calls, Telegram, risk math, order send, fitted QRF.  
Not trade-ready. Live trading is disabled. Python 3.11+ required.
