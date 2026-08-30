"""Emit Sequence 14 observability evidence. Not a trading path."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Emit Sequence 14 evidence")
    parser.add_argument("--out-dir", default=str(ROOT / "docs" / "evidence" / "seq14"))
    parser.add_argument("--desk-json", default=str(ROOT / "public" / "observability.json"))
    args = parser.parse_args(argv)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    from botmoduleproject1.app.bootstrap import bootstrap
    from botmoduleproject1.modules.observability.errors import ERROR_CATALOG
    from botmoduleproject1.modules.observability.metrics import METRIC_CATALOG
    from botmoduleproject1.modules.observability.redaction import redact_mapping, safe_json
    from botmoduleproject1.modules.observability.runbooks import RUNBOOKS, write_markdown

    now = datetime.now(timezone.utc).isoformat()
    yaml = ROOT / "configs" / "test.example.yaml"
    settings, container, runtime = bootstrap(config_path=yaml, cli_mode="observe", environ={})
    obs = container.registry.get("observability").instance
    snap = obs.snapshot(settings, lifecycle=runtime.container.lifecycle.state)
    payload = redact_mapping(snap.model_dump(mode="json"))
    blob = json.dumps(payload, indent=2, sort_keys=True)
    dump_checksum = _sha(blob)
    canonical = _sha(json.dumps({"trading_readiness": False, "accept_trade": False}, sort_keys=True))

    (out / "observability_snapshot.json").write_text(blob + "\n", encoding="utf-8")
    desk = Path(args.desk_json)
    desk.parent.mkdir(parents=True, exist_ok=True)
    desk.write_text(blob + "\n", encoding="utf-8")

    (out / "interpreter.txt").write_text(
        f"utc={now}\npython={sys.version}\nexecutable={sys.executable}\n",
        encoding="utf-8",
    )
    metrics_blob = json.dumps(
        [s.model_dump(mode="json") for s in METRIC_CATALOG],
        indent=2,
        sort_keys=True,
    )
    (out / "metrics_catalog.json").write_text(metrics_blob + "\n", encoding="utf-8")
    (out / "error_catalog.json").write_text(
        json.dumps([s.model_dump(mode="json") for s in ERROR_CATALOG], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(ROOT / "docs" / "runbooks")
    (out / "runbook_ids.txt").write_text("\n".join(rb.runbook_id for rb in RUNBOOKS) + "\n", encoding="utf-8")
    (out / "checksums.txt").write_text(
        "\n".join(
            [
                f"# Sequence 14 evidence  utc={now}",
                "# dump checksum is run-specific (timestamps/UUIDs in snapshot).",
                f"dump_sha256={dump_checksum}",
                f"payload_canonical_sha256={canonical}",
                "trading_readiness=false",
                "accept_trade=false",
                f"metric_catalog_count={len(METRIC_CATALOG)}",
                f"runbook_count={len(RUNBOOKS)}",
                f"error_catalog_count={len(ERROR_CATALOG)}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (out / "redaction_sample.json").write_text(
        safe_json({"password": "should-never-appear", "note": "ok"}) + "\n",
        encoding="utf-8",
    )
    runtime.stop()
    print(out / "observability_snapshot.json")
    print(desk)
    return 0 if payload["health"]["trading_readiness"] is False else 1


if __name__ == "__main__":
    raise SystemExit(main())
