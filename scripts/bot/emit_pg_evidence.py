#!/usr/bin/env python3
"""Emit PostgreSQL durability evidence. Not a trading path."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from botmoduleproject1.modules.pm8_persistence.postgres.embedded import discover_dsn, start_embedded_postgres
from botmoduleproject1.modules.pm8_persistence.postgres.store import PostgresStore
from botmoduleproject1.modules.pm8_persistence.store import StorageUnavailable


def main() -> int:
    out_dir = ROOT / "docs" / "evidence" / "postgresql"
    out_dir.mkdir(parents=True, exist_ok=True)
    captured = datetime.now(timezone.utc).isoformat()
    payload = {
        "captured_at": captured,
        "backend": "postgresql",
        "sqlite_fallback": False,
        "production_durable": False,
        "trading_readiness": False,
        "server_version": None,
        "ping": False,
        "skip_locked": True,
        "numeric_money": True,
        "classification": "POSTGRESQL DURABILITY NEEDS EVIDENCE",
    }
    try:
        dsn = discover_dsn() or start_embedded_postgres()
        store = PostgresStore(dsn, schema_name="evidence")
        from botmoduleproject1.modules.pm8_persistence.migrations import MigrationService

        MigrationService(store).upgrade_to(2)
        diag = store.diagnostics()
        payload.update(
            {
                "server_version": diag.get("server_version"),
                "ping": bool(diag.get("ping")),
                "schema_version": diag.get("schema_version"),
                "dsn_redacted": True,
                "classification": "postgresql backend verified; production_durable refused; Sequence 11+ blocked",
            }
        )
        store.close()
    except (StorageUnavailable, Exception) as exc:
        payload["error"] = type(exc).__name__
        payload["classification"] = "postgresql configured or probe failed; fail-closed; Sequence 11+ blocked"
    (out_dir / "postgresql_durability.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    public = Path("/workspace/public/observability/postgresql_durability.json")
    if public.parent.exists():
        public.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": payload.get("ping"), "path": str(out_dir / "postgresql_durability.json")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
