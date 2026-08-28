def by_order(records, order_id: str):
    return [r for r in records if r.order_id == order_id]

def by_session(records, session_id: str):
    return [r for r in records if r.session_id == session_id]

def by_symbol(records, symbol: str):
    return [r for r in records if r.symbol == symbol]
