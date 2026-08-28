def ordered(records) -> bool:
    seq = [r.sequence for r in records]
    return seq == sorted(seq) and len(seq) == len(set(seq))
