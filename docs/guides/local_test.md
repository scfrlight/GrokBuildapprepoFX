# Local test guide

```text
PYTHONPATH=. .venv311/bin/python -m pytest tests --tb=short
PYTHONPATH=. .venv311/bin/python scripts/bot/emit_evidence.py --out-dir docs/evidence
PYTHONPATH=. .venv311/bin/python scripts/bot/emit_seq14_evidence.py --out-dir docs/evidence/seq14
PYTHONPATH=. python3.10 -m botmoduleproject1 doctor --profile test --config configs/test.example.yaml
# expect exit 1 and STARTUP FAILED
```
