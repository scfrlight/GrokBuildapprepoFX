# Metrics catalog

Canonical names live in `botmoduleproject1.modules.observability.metrics.METRIC_CATALOG`.

Each spec has: name, type (counter/gauge/histogram), unit, labels, cardinality policy, source module, update point, safe default (0), description.

Allowed label keys: `module`, `profile`, `dimension`, `error_code`, `family`, `outcome`, `probe`. Values ≤ 32 chars. No secrets, payloads, full IDs, stack traces, or unbounded symbols.

Unknown names and illegal labels raise. Safe default for an unseen metric is `0`.
