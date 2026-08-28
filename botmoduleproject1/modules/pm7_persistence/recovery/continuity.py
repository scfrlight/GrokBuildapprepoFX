def continuity_ok(records) -> bool:
    expected = 1
    for rec in records:
        if rec.sequence != expected:
            return False
        expected += 1
    return True
