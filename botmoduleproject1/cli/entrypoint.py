"""CLI entry point. Modes: test, doctor, paper, live, backfill.

ADR-008: assert_python_version() runs before any pydantic/settings import.
`app/__init__.py` is lazy so `python -m botmoduleproject1` on Python <3.11
fails with PythonVersionError, not ImportError.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from botmoduleproject1.app.exceptions import (
    LiveTradingDisabledError,
    PlatformError,
    PreflightError,
    PythonVersionError,
    SettingsError,
)
from botmoduleproject1.app.python_version import assert_python_version


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
    parser.add_argument(
        "--profile",
        dest="profile",
        default=None,
        help="demo | test | backtest | research | live (live is recognized and refused)",
    )
    parser.add_argument(
        "--env-file",
        dest="env_file",
        default=None,
        help="optional .env path; only prefixed and allowlisted keys are read",
    )
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


def _normalize_mode(raw: str) -> str:
    alias = {
        "dry-run": "paper",
        "observe_only": "observe-only",
        "live_disabled": "live-disabled",
    }
    mode = alias.get(raw, raw)
    if mode not in _ALLOWED_MODES and mode not in alias.values():
        raise SystemExit(f"unknown mode {raw!r}")
    return mode


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    mode = _normalize_mode(str(args.mode))
    try:
        assert_python_version()
        from botmoduleproject1.app.bootstrap import bootstrap

        settings, _container, runtime = bootstrap(
            config_path=args.config,
            cli_mode=mode,
            heartbeat_ticks=int(args.heartbeat),
            profile=args.profile,
            env_file=args.env_file,
        )
        snapshot = runtime.last_snapshot
        assert snapshot is not None
        if args.json:
            print(json.dumps(snapshot.model_dump(mode="json"), indent=2, sort_keys=True))
        else:
            print("\n".join(snapshot.banner_lines()))
            print(f"fingerprint={settings.fingerprint()}")
            print(f"profile={settings.profile.value}")
            caps = ", ".join(c.value for c in settings.profile_policy.allowed_capabilities)
            print(f"allowed_capabilities={caps}")
        runtime.stop()
        return 0
    except LiveTradingDisabledError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except PythonVersionError as exc:
        print(f"STARTUP FAILED: {exc}", file=sys.stderr)
        return 1
    except (SettingsError, PreflightError, PlatformError) as exc:
        print(f"STARTUP FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
