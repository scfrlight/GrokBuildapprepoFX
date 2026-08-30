# CI run 33305725241 (commit ce0aa74d77125345889d1554d1a0cec6ef576d3b)

Committed copies of GitHub Actions artifacts so verification does not require
artifact-download login. Source run: public repo
https://github.com/scfrlight/GrokBuildapprepoFX/actions/runs/33305725241

Jobs (all conclusion=success):
- pytest (CPython 3.11) job 99241836256
- pytest (CPython 3.12) job 99241836109
- doctor fail-fast on CPython 3.10 (no deps) job 99241836177

doctor-3.11.out / doctor-3.12.out are the **plain stdout banner** from the
job log (the workflow at ce0aa74 did not yet tee doctor to a file). pytest
and backup/restore files are byte copies of the uploaded artifacts.
