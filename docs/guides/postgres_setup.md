# PostgreSQL setup

## Environment

```
BOTMODULEPROJECT1_DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DBNAME
```

Unprefixed `DATABASE_URL` is ignored (PaaS pollution).

YAML (`pm8_persistence`):

```yaml
pm8_persistence:
  operating_mode: postgresql
  sslmode: prefer
  connect_timeout_seconds: 5
  statement_timeout_ms: 30000
  pool_min: 1
  pool_max: 8
  schema_name: public
  production_durable: false
```

Feature flag `enable_pm8_persistence` stays YAML-default false.

## Fail-closed

If `operating_mode=postgresql` and the DSN is missing or the server is down, startup raises `StorageUnavailable`. SQLite is not substituted.

## Local / sandbox

This sandbox can start the pgserver 16.2 binary in a user namespace (PostgreSQL refuses uid 0):

```
PYTHONPATH=. python -c "from botmoduleproject1.modules.pm8_persistence.postgres.embedded import start_embedded_postgres; print(start_embedded_postgres())"
```

CI uses the `postgres:16` service on GitHub Actions with the prefixed DSN.

## SSL

`sslmode`: disable|allow|prefer|require|verify-ca|verify-full. Default `prefer`. Production operators should use `require` or stricter; this repo still refuses `production_durable=true`.
