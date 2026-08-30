"""Execution boundary: capital output never becomes a broker call."""

FORBIDDEN_SURFACE = frozenset(
    {
        "submit",
        "order_send",
        "OrderSend",
        "MetaTrader5",
        "telegram",
        "broker_commands",
    }
)


def execution_allowed() -> bool:
    return False


def trading_readiness() -> bool:
    return False
