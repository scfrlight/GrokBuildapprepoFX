def event_ids(records):
    return tuple(str(r.event.event_id) for r in records)
