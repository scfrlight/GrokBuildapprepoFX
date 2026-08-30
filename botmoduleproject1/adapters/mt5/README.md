# MT5 adapter

Sequence 07 placeholder (`ems/mt5_adapter.Mt5BrokerAdapter`) stays blocked.

Sequence 11 Demo gateway (`demo_gateway.DemoMt5Gateway`) is simulated-only in
this environment. Tickets are `DEMO-*` and are not broker truth. Live account
kind is refused. Linux without a terminal is fail-closed unless `simulated=True`.

Must not import pm3_strategy_engine. Entry logic must not call the gateway;
use `pm5_execution.demo_routing.DemoRouter` after a PM4 ALLOW.
