"""CI / evidence hygiene for Sequence 14. Fail the suite if pipelines can hide errors."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"
EVIDENCE = ROOT / "docs" / "evidence"

SECRET_NEEDLES = (
    "TELEGRAM_BOT_TOKEN=",
    "MT5_PASSWORD=",
    "BEGIN RSA PRIVATE KEY",
    "postgres://",
    "postgresql://",
)


def _run_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    in_run = False
    for line in text.splitlines():
        if re.match(r"\s+run:\s*\|", line):
            if current:
                blocks.append("\n".join(current))
            current = [line]
            in_run = True
            continue
        if in_run:
            if line.strip() == "" or line.startswith("          ") or line.startswith("            ") or line.startswith("        "):
                # still in the block if indented more than `run:`
                if re.match(r"^\s{2}-\sname:", line) or re.match(r"^\s{2}- uses:", line) or re.match(r"^[a-z]", line):
                    blocks.append("\n".join(current))
                    current = []
                    in_run = False
                else:
                    current.append(line)
            else:
                blocks.append("\n".join(current))
                current = []
                in_run = False
    if current:
        blocks.append("\n".join(current))
    return blocks


def test_workflows_pipefail_on_pipelines():
    files = list(WORKFLOWS.glob("*.yml")) + list(WORKFLOWS.glob("*.yaml"))
    assert files, "no workflow files"
    offenders: list[str] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if stripped.endswith("|") or stripped.endswith("|-") or stripped.endswith("|+"):
                continue
            if "| tee" in line or "| grep" in line:
                window = "\n".join(text.splitlines()[max(0, i - 8) : i])
                if "pipefail" not in window:
                    offenders.append(f"{path.name}:{i}:{stripped}")
    assert offenders == [], f"piped commands without pipefail: {offenders}"


def test_set_plus_e_restores_errexit():
    text = (WORKFLOWS / "tests.yml").read_text(encoding="utf-8")
    if "set +e" in text:
        # every set +e must be followed by set -e before assertions
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if "set +e" in line:
                following = "\n".join(lines[i : i + 20])
                assert "set -e" in following, "set +e without restoring set -e"
                assert "code=$?" in following or "code = $?" in following


def test_numbering_map_on_disk_00_14():
    text = (ROOT / "docs" / "MODULE_NUMBERING_MAP.md").read_text(encoding="utf-8")
    for n in range(15):
        assert f"| {n:02d} |" in text


def test_evidence_has_no_secret_values():
    if not EVIDENCE.exists():
        return
    leaks: list[str] = []
    for path in EVIDENCE.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix in {".sqlite", ".sqlite3", ".png", ".jpg"}:
            continue
        try:
            blob = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for needle in SECRET_NEEDLES:
            if needle in blob:
                leaks.append(f"{path}:{needle}")
    assert leaks == [], f"secret material in evidence: {leaks}"


def test_live_command_fail_closed_in_hygiene():
    from botmoduleproject1.cli.entrypoint import main
    from botmoduleproject1.app.bootstrap import bootstrap
    from botmoduleproject1.app.exceptions import LiveTradingDisabledError

    yaml = ROOT / "configs" / "test.example.yaml"
    assert main(["live", "--config", str(yaml)]) == 2
    try:
        bootstrap(config_path=yaml, cli_mode="live", environ={})
        raise AssertionError("live bootstrap must fail")
    except LiveTradingDisabledError:
        pass
