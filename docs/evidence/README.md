# Evidence

Independent verification artifacts for Sequences 09–13. Numbers in audits
must cite a file here or a GitHub Actions run URL.

## Reproduce

```text
# Official suite — Python 3.11+ clean venv
python3.11 -m venv .venv311
.venv311/bin/python -m pip install -r requirements-dev.txt
PYTHONPATH=. .venv311/bin/python --version
PYTHONPATH=. .venv311/bin/python -m pytest tests --tb=short -q | tee docs/evidence/pytest-3.11.log

# Restart drill + backup checksum (raw logs)
PYTHONPATH=. .venv311/bin/python scripts/bot/emit_evidence.py --out-dir docs/evidence

# Fail-fast on the sandbox 3.10 interpreter (must exit 1, no pydantic required)
PYTHONPATH=. python3.10 -m botmoduleproject1 doctor --profile test --config configs/test.example.yaml
```

CI: `.github/workflows/tests.yml` (matrix 3.11 / 3.12 + a 3.10 fail-fast job).

## Files

| File | What |
|---|---|
| `interpreter.txt` | `sys.version` of the evidence run |
| `restart_drill.log` | raw RestartDrill output |
| `backup_restore.log` | checksum + verified + sequence unchanged |
| `pytest-3.11.log` | local official suite transcript |
| `doctor_py310_fail_fast.log` | local 3.10 doctor stderr |
| `doctor_py311.log` | local 3.11 doctor stdout |
