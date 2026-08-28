def timeline(records):
    return tuple(f"{r.sequence}:{r.event.event_type}" for r in records)
