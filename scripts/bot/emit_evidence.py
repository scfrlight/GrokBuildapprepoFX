"""Write raw Sequence 10 backup/restore and restart-drill logs.

Not a trading path. Safe to run in CI.

Backup checksum is sha256 of dump_events_json() for THIS run. It is not a
golden hash across environments: event_id, correlation_id, occurred_at and
row_hash are generated per ingest. Restore proves the file matches the
checksum of that dump, not that two machines produced identical bytes.

payload_canonical_sha256 hashes only payload_json fields and IS comparable
across runs (same business payload → same value).
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def payload_canonical_sha256(blob: str) -> str:
    events = json.loads(blob)
    payloads = [row.get("payload_json") for row in events]
    return sha256(json.dumps(payloads, sort_keys=True).encode("utf-8")).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Emit persistence evidence logs")
    parser.add_argument("--out-dir", default=str(ROOT / "docs" / "evidence"))
    args = parser.parse_args(argv)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    from botmoduleproject1.contracts.v1.pm8_persistence import TableFamily
    from botmoduleproject1.modules.pm8_persistence.api.v1 import PersistenceApiV1
    from botmoduleproject1.modules.pm8_persistence.migrations import (
        MigrationService,
        RestartDrill,
        RestoreService,
    )
    from botmoduleproject1.modules.pm8_persistence.store import SqliteStore

    now = datetime.now(timezone.utc).isoformat()
    drill_path = out / "restart_drill.log"
    backup_path = out / "backup_restore.log"
    meta_path = out / "interpreter.txt"

    meta_path.write_text(
        f"utc={now}\npython={sys.version}\nexecutable={sys.executable}\n",
        encoding="utf-8",
    )

    work = out / "_scratch"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(exist_ok=True)
    result = RestartDrill().run(work / "drill.sqlite")
    drill_body = [
        f"# restart drill  utc={now}",
        f"# command: PYTHONPATH=. python scripts/bot/emit_evidence.py --out-dir {out}",
        f"passed={result['passed']!r}",
        f"sequence={result.get('sequence')!r}",
        "log:",
    ]
    drill_body.extend(f"  {line}" for line in result["log"])
    drill_path.write_text("\n".join(drill_body) + "\n", encoding="utf-8")

    store = SqliteStore(work / "live.sqlite")
    MigrationService(store).upgrade_to(2)
    api = PersistenceApiV1(store)
    api.ingest_event(event_type="t", producer="evidence", family=TableFamily.EVENT, payload={"n": 7})
    before = store.last_sequence()
    report = api.backup(work / "backups")
    RestoreService(store).verify_file(Path(report.path), report.checksum)
    after = store.last_sequence()
    blob = Path(report.path).read_text(encoding="utf-8")
    payload_hash = payload_canonical_sha256(blob)
    backup_body = [
        f"# backup / restore verification  utc={now}",
        f"# command: PYTHONPATH=. python scripts/bot/emit_evidence.py --out-dir {out}",
        f"schema_version={getattr(report, 'schema_version', 'v1')}",
        f"backup_id={report.backup_id}",
        f"checksum={report.checksum}",
        "# checksum = sha256(dump_events_json()); dump includes event_id, correlation_id,",
        "# occurred_at, row_hash. It is run-specific, not a golden cross-run hash.",
        f"payload_canonical_sha256={payload_hash}",
        "# payload_canonical_sha256 hashes only payload_json fields and IS comparable.",
        f"path={report.path}",
        f"verified={report.verified}",
        f"event_count={report.event_count}",
        f"sequence_before={before}",
        f"sequence_after_verify={after}",
        f"runtime_untouched={before == after}",
    ]
    backup_path.write_text("\n".join(backup_body) + "\n", encoding="utf-8")
    print(drill_path)
    print(backup_path)
    print(meta_path)
    return 0 if result["passed"] and report.verified and before == after else 1


if __name__ == "__main__":
    raise SystemExit(main())
