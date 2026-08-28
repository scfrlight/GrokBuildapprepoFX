# PM4 — exclusive risk gate

Implementation: `botmoduleproject1/modules/pm4_risk_gate/`.

This package is a compatibility re-export so Sequence 01 registry name `pm4_risk`
stays stable. Only `pm4_risk_gate` contains business logic.

Deny-by-default. ALLOW is not an order. PM5 remains closed.
