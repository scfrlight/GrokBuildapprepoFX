def apply_filters(records, spec):
    items = list(records)
    if spec.trace_id:
        items = [r for r in items if str(r.event.trace_id) == spec.trace_id]
    if spec.session_id:
        items = [r for r in items if r.event.session_id == spec.session_id]
    if spec.symbol:
        items = [r for r in items if r.event.symbol == spec.symbol]
    if spec.strategy_id:
        items = [r for r in items if r.event.strategy_id == spec.strategy_id]
    if spec.order_id:
        items = [r for r in items if r.event.order_id == spec.order_id]
    if spec.incident_id:
        items = [r for r in items if r.event.incident_id == spec.incident_id]
    if spec.category is not None:
        items = [r for r in items if r.event.category is spec.category]
    return items
