from botmoduleproject1.modules.pm7_persistence.journal.append_only import AppendOnlyJournal


class JournalService:
    def __init__(self, backend: AppendOnlyJournal) -> None:
        self.backend = backend

    def append(self, event, *, now, durable: bool = False):
        return self.backend.append(event, now=now, durable=durable)

    def get(self, event_id):
        return self.backend.get(event_id)

    def records(self):
        return self.backend.records()
