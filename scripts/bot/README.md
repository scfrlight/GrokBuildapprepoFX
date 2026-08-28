# Operator scripts

## Windows

`start.bat` activates `.venv` if present and runs `python -m botmoduleproject1`.

```text
scripts\bot\start.bat doctor --config configs\test.example.yaml
scripts\bot\start.bat live
```

`live` is recognized and refused. Logs append to `logs\platform.*.log`.

Never put tokens on the command line. Never send orders from this folder.
