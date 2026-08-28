def counts(records) -> dict:
    by_mod = {}
    for r in records:
        by_mod[r.event.source_module] = by_mod.get(r.event.source_module, 0) + 1
    return by_mod
