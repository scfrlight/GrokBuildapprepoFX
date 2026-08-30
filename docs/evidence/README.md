# Evidence

Independent verification artifacts for Sequences 09–13. Numbers in audits
must cite a file here, a file under `ci/`, or the full inline body in the
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
PYTHONPATH=. .venv311/bin/python -m pytest tests --tb=short -q | tee docs/evidence/pytest-3.11.log

# Restart drill + backup checksum (raw logs)
PYTHONPATH=. .venv311/bin/python scripts/bot/emit_evidence.py --out-dir docs/evidence

# Fail-fast on the sandbox 3.10 interpreter (must exit 1, no pydantic required)
PYTHONPATH=. python3.10 -m botmoduleproject1 doctor --profile test --config configs/test.example.yaml
```

CI: `.github/workflows/tests.yml` (matrix 3.11 / 3.12 + a 3.10 fail-fast job).

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

| Run | backup_id | dump checksum (sha256 of events JSON) |
|---|---|---|
| local 3.11.2 `/workspace/.venv311` 2026-08-30T10:03:43Z | `88e37a17-18ab-4085-bc26-065d17f36ba6` | `b6fbdca7477fceb31cfe2777e4839be14184f6742e7af551dee8383ac6e6802d` |
| CI 3.11.16 run 33305725241 | `fa387454-31bb-420f-bf8a-aa953a8aba41` | `bd5bb00c1243c7f3e951d019791b22ae9336272770174bfa2a0abb4775d28949` |
| CI 3.12.14 run 33305725241 | `76ba714b-30ef-4770-9d5f-0f64c43871dc` | `ec4bcff2eff9fe8e928a53e63dfe2e1b0a7a2afc5d5723693e3c44cafd31a225` |

All three dumps carry `payload_json = {"n": 7}`. All three reported
`verified=True` and `sequence_before=1` / `sequence_after_verify=1`.

**Invariant that restore actually proves (per run):**

1. `sha256(backup_file_bytes) == report.checksum`
2. `RestoreService.verify_file(path, report.checksum)` succeeds
3. live `last_sequence()` is unchanged (`runtime_untouched=True`)

**Not an invariant:** `checksum(local) == checksum(CI)`.

Seeds are **not** frozen: a frozen dump hash would hide the fact that
production backups bind identity + time. The comparable field is
`payload_canonical_sha256` (hash of `payload_json` only), emitted by
`scripts/bot/emit_evidence.py` from this commit onward.

`tests/unit/test_pm8a_seq10.py::test_backup_checksum_is_dump_specific_not_golden`
asserts two independent `{"n": 7}` backups have different dump checksums,
identical payload JSON, and each restores against its own checksum.

## Files

| File | What |
|---|---|
| `interpreter.txt` | `sys.version` of the evidence run |
| `restart_drill.log` | raw RestartDrill output |
| `backup_restore.log` | dump checksum + payload_canonical_sha256 + verified + sequence unchanged |
| `pytest-3.11.log` | local official suite transcript |
| `doctor_py310_fail_fast.log` | local 3.10 doctor stderr |
| `doctor_py311.log` | local 3.11 doctor stdout |
| `ci/run-33305725241/` | committed copies of CI artifacts so they are fetchable without Actions login |
