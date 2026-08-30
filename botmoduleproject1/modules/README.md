# Bounded context packages

One folder per PM. Cross-talk only via `contracts`.

Name source of truth: `docs/MODULE_NUMBERING_MAP.md`.

`pm4_risk` is a compatibility re-export. Implementation: `pm4_risk_gate`.
`pm6_monitoring` is a compatibility re-export. Implementation: `pm6_post_trade`.
`pm7_ledger` is a compatibility re-export. Implementation: `pm7_persistence`.
`pm9_operator_ux` is a compatibility re-export. Implementation: `pm8_operator`.

Sequence 11 is **`mt5_execution_engine`**. It is not PM6. `pm6_post_trade` remains the only PM6 package.
