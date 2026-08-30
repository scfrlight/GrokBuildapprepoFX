# PM4 capital-gate evidence

Not Sequence 15. Not a trading enablement bundle.

| File | What |
|---|---|
| `pytest-3.11.log` | Full suite after capital hardening (624 passed on this host) |
| `pytest-junit.xml` | JUnit for the same run |
| `pm4_capital_gate.json` | Exported ops snapshot (also served at `/observability/pm4_capital_gate.json`) |
| `doctor-3.11.out` | Supported interpreter |
| `doctor-3.10.err` | ADR-008 fail-fast |
| `live.err` | Live CLI refuse |
| `interpreter.txt` | CPython 3.11.2 |
| `checksums.txt` | SHA-256 of the files above |

No DSN, tokens, or private keys. `production_durable` is not claimed. `trading_readiness` is false.
