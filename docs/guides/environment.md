# Environment guide

Python 3.11+ (ADR-008). Official suite: 3.11 and 3.12. Python 3.10 must fail-fast with `STARTUP FAILED` before pydantic.

```text
python3.11 -m venv .venv311
.venv311/bin/python -m pip install -r requirements-dev.txt
PYTHONPATH=. .venv311/bin/python -m botmoduleproject1 doctor --profile test --config configs/test.example.yaml
```
