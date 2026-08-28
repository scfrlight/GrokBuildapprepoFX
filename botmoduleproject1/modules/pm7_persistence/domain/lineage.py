from botmoduleproject1.contracts.v1.persistence import LedgerEvent


def lineage_of(event: LedgerEvent) -> tuple[str, ...]:
    refs = list(event.lineage_refs)
    if event.causation_id is not None:
        refs.append(str(event.causation_id))
    refs.append(str(event.event_id))
    return tuple(dict.fromkeys(refs))
