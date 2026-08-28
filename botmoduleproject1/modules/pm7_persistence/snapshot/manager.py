from botmoduleproject1.contracts.v1.persistence import SnapshotState
from botmoduleproject1.modules.pm7_persistence.snapshot.capture import capture
from botmoduleproject1.modules.pm7_persistence.snapshot.validation import validate_checksum


class SnapshotService:
    def __init__(self) -> None:
        self.items = []

    def capture(self, *, now, records, scope):
        if self.items:
            last = self.items[-1]
            self.items[-1] = last.model_copy(update={"state": SnapshotState.SUPERSEDED})
        snap = capture(now=now, records=records, scope=scope)
        checked = validate_checksum(snap)
        snap = snap.model_copy(update={"state": checked})
        self.items.append(snap)
        return snap
