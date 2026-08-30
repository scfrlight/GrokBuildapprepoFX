# Evidence

Independent verification artifacts for Sequences 09–14 plus PM4 capital hardening.
Numbers in audits must cite a file here, a file under `ci/`, or the full inline body in the
audit report. GitHub Actions **artifact ZIPs require login** even on a
public repo; that is why CI transcripts are also committed under `ci/`
and duplicated inline in the architect report.

## Visibility

| Surface | Auth required? | How checked 2026-08-30 |
|---|---|---|
| `https://github.com/scfrlight/GrokBuildapprepoFX` | no | `curl -sI` → HTTP 200; `gh repo view --json visibility` → `PUBLIC` |
| `/actions` tab | no | `curl -sI` → HTTP 200 |
| run `33305725241` HTML | no | `curl -sI` → HTTP 200; job names visible in HTML |
| `raw.githubusercontent.com/.../docs/evidence/*` | no | `curl -sI` → HTTP 200 |
| Actions **artifact download** | **yes** (GitHub login) | documented limitation; mitigated by `ci/` copies + inline logs |

## Reproduce

```text
# Official suite — Python 3.11+ clean venv
python3.11 -m venv .venv311
.venv311/bin/python -m pip install -r requirements-dev.txt
PYTHONPATH=. .venv311/bin/python --version
set +e
PYTHONPATH=. .venv311/bin/python -m pytest tests --tb=short > docs/evidence/pytest-3.11.log 2>&1
code=$?
set -e
test "$code" -eq 0
# Do not use `pytest | tee` or `command | grep` as a success gate.

# Restart drill + backup checksum (raw logs)
PYTHONPATH=. .venv311/bin/python scripts/bot/emit_evidence.py --out-dir docs/evidence

# Sequence 14 observability snapshot
PYTHONPATH=. .venv311/bin/python scripts/bot/emit_seq14_evidence.py --out-dir docs/evidence/seq14

# Fail-fast on the sandbox 3.10 interpreter (must exit 1, no pydantic required)
PYTHONPATH=. python3.10 -m botmoduleproject1 doctor --profile test --config configs/test.example.yaml
```

Reconciliation 2026-08-30 evidence: `docs/evidence/reconciliation/`.


CI: `.github/workflows/tests.yml` (matrix 3.11 / 3.12 + 3.10 fail-fast + seq14-hygiene).

## Backup checksum is NOT a golden cross-run hash

`PersistenceApiV1.backup()` sets

```text
checksum = sha256(dump_events_json().encode("utf-8")).hexdigest()
```

`dump_events_json()` serializes full event rows (`json.dumps(..., sort_keys=True)`).
Each `ingest_event` generates a new `event_id`, `correlation_id`, `occurred_at`
and `row_hash`. Therefore **two evidence runs with the same business payload
`{"n": 7}` MUST produce different dump checksums.** That is expected. It is
not a restore bug.

**Invariant that restore actually proves (per run):**

1. `sha256(backup_file_bytes) == report.checksum`
2. `RestoreService.verify_file(path, report.checksum)` succeeds
3. live `last_sequence()` is unchanged (`runtime_untouched=True`)

**Not an invariant:** `checksum(local) == checksum(CI)`.

The comparable field is `payload_canonical_sha256` (hash of `payload_json` only).

## Sequence 14 snapshot checksum

`docs/evidence/seq14/checksums.txt` records `dump_sha256` (run-specific; the
snapshot contains `captured_at` and generated IDs) and
`payload_canonical_sha256` of `{trading_readiness: false, accept_trade: false}`.

## Files

| File | What |
|---|---|
| `interpreter.txt` | `sys.version` of the evidence run |
| `restart_drill.log` | raw RestartDrill output |
| `backup_restore.log` | checksum + verified + sequence unchanged |
| `pytest-3.11.log` | local official suite transcript |
| `doctor_py310_fail_fast.log` | local 3.10 doctor stderr |
| `doctor_py311.log` | local 3.11 doctor stdout |
| `seq14/` | observability snapshot, catalogs, redaction sample |
| `ci/run-33305725241/` | committed copies of CI artifacts from ce0aa74 |
| `ci/run-33307496179/` | Sequence 14 CI: 3.11/3.12 526 passed, hygiene, live fail-closed, 3.10 fail-fast |
