# MT5 adapter (transport)

Sequence 07 placeholder (`pm5_execution.ems.mt5_adapter.Mt5BrokerAdapter`) stays blocked.

Sequence 11 Demo gateway (`demo_gateway.DemoMt5Gateway`) is simulated-only.
Tickets are `DEMO-*` and are not broker truth. Live account kind is refused.

**Package for routing and exits:** `botmoduleproject1.modules.mt5_execution_engine`
(not `pm5_execution`, not `pm6`). Entry logic must not call the gateway;
use `DemoRouter` after a PM4 ALLOW.

See `docs/MODULE_NUMBERING_MAP.md`.
