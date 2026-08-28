"""CLI entry point. Modes: test, doctor, paper, live, backfill."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from botmoduleproject1.app.exceptions import LiveTradingDisabledError, PlatformError, SettingsError
from botmoduleproject1.app.settings import CliMode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="botmoduleproject1",
        description="BotModuleProject1 platform kernel. Not a trading terminal.",
    )
    parser.add_argument(
        "mode",
        nargs="?",
        default="doctor",
        help="test | doctor | paper | live | backfill | demo | observe-only",
    )
    parser.add_argument("--config", dest="config", default=None, help="YAML config path")
    parser.add_argument("--json", action="store_true", help="print diagnostics as JSON")
    parser.add_argument(
        "--heartbeat",
        type=int,
        default=0,
        help="optional heartbeat ticks after boot (0 = self-test, no loop)",
    )
    return parser


_ALLOWED_MODES = {
    "test",
    "doctor",
    "paper",
    "live",
    "backfill",
    "demo",
    "observe-only",
    "research",
    "backtest",
    "live-disabled",
    "dry-run",
}


def _normalize_mode(raw: str) -> CliMode:
    alias = {
        "dry-run": "paper",
        "observe_only": "observe-only",
        "live_disabled": "live-disabled",
    }
    mode = alias.get(raw, raw)
    if mode not in _ALLOWED_MODES and mode not in alias.values():
        raise SystemExit(f"unknown mode {raw!r}")
    return mode  # type: ignore[return-value]


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    mode = _normalize_mode(str(args.mode))
    try:
        from botmoduleproject1.app.bootstrap import bootstrap

        settings, _container, runtime = bootstrap(
            config_path=args.config,
            cli_mode=mode,
            heartbeat_ticks=int(args.heartbeat),
        )
        snapshot = runtime.last_snapshot
        assert snapshot is not None
        if args.json:
            print(json.dumps(snapshot.model_dump(mode="json"), indent=2, sort_keys=True))
        else:
            print("\n".join(snapshot.banner_lines()))
            print(f"fingerprint={settings.fingerprint()}")
        runtime.stop()
        return 0
    except LiveTradingDisabledError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except (SettingsError, PlatformError) as exc:
        print(f"STARTUP FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
