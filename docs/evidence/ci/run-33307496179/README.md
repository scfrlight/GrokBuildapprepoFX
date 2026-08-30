# CI run 33307496179 (commit 6c4f0d2937bb9f4d9d577df528ae47890a294e4b)

Committed copies of GitHub Actions artifacts so verification does not require
artifact-download login. Source run (public):
https://github.com/scfrlight/GrokBuildapprepoFX/actions/runs/33307496179

Jobs (all conclusion=success):

| Job | ID | Duration |
|---|---|---|
| pytest (CPython 3.11) | 99246508814 | 21s |
| pytest (CPython 3.12) | 99246508800 | 22s |
| Sequence 14 safety hygiene | 99246508737 | 15s |
| doctor fail-fast on CPython 3.10 (no deps) | 99246508836 | 4s |

Counts from the committed pytest logs (not from the GitHub UI summary):

- `pytest-3.11.log`: `526 passed in 4.94s` on CPython 3.11.16
- `pytest-3.12.log`: `526 passed in 4.92s` on CPython 3.12.14
- `hygiene.log`: `14 passed in 0.53s`
- `doctor_py310.err`: `STARTUP FAILED: Python 3.10.21 is not supported`
- `live.err`: `LIVE TRADING IS DISABLED.`

`seq14-checksums-*.txt` dump hashes are run-specific. `payload_canonical_sha256`
is `8c6737b844e22b710214f59468264041b2a00901c80cc8611811f25984c566a2` on both
matrix legs (`trading_readiness=false`, `accept_trade=false`).
