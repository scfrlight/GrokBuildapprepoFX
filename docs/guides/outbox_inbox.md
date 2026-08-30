# Outbox / inbox

Business mutation and outbox insert share one transaction.

## Outbox relay

`relay_outbox` claims rows (`pending`/`failed` or expired lease) then publishes through `OutboxPublisher`.

States: pending → claimed → published | failed | dead-letter.

SQLite relay is **local/test-only**. PostgreSQL multi-worker concurrency (`FOR UPDATE SKIP LOCKED`) is **BLOCKED**.

No broker SDK is imported by PM8.

## Inbox

`consume_inbox` records `received`, runs the handler, then `processed`. Handler failure is retryable; exhausted attempts become dead-letter. Duplicate processed ids are ignored.

## Idempotency

Same key + same request hash → stored result. Same key + different hash → `IdempotencyConflict`.
