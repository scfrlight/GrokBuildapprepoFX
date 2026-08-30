# CI guide

Workflow: `.github/workflows/tests.yml`

- pytest matrix CPython 3.11 / 3.12; pytest exit captured (`set +e` / `code=$?` / `test "$code" -eq 0`). `pytest | tee` and `command | grep` are forbidden as success gates.

- doctor on the supported interpreter
- evidence emission (failure fails the job)
- doctor fail-fast on 3.10 without deps (`set +e` then `set -e` and `test "$code" -eq 1`)
- seq14-hygiene: unsafe pipelines, secrets in evidence, docs paths, numbering 00–14, live fail-closed

Artifact ZIPs require GitHub login even on a public repo. Transcripts are also committed under `docs/evidence/`.
