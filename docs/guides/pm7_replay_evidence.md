# PM7 replay and evidence

Sqlite/file backends reload the journal after restart. Snapshots and evidence bundles are persisted as sidecars and reloaded with the module.

- Replay does not mutate source history.
- Snapshot checksum covers journal high-watermark + payload.
- Evidence bundles reference source event ids.
- Freeze blocks purge.
- Export package checksums the canonical payload.
- PM7 remains a **PARTIAL** warehouse vs a missing `PM7_Master_Prompt.md` (**SOURCE-MISSING**). Canonical downstream API is still PM8 `PersistenceApiV1`.
