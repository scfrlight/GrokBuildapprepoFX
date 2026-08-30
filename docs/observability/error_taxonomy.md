# Error taxonomy

Canonical codes: `botmoduleproject1.contracts.v1.observability.ErrorCode`.

Each code has severity, retryable, operator action, system action, whether trading must halt, audit requirement, and a public-safe message. Operator-facing text must not include traceback, secrets, or internal filesystem paths.

`UNEXPECTED_INTERNAL_ERROR` public message: "Internal error. Trading remains halted."
