# mt5_execution_engine (Sequence 11)

Canonical package for **Demo-only MT5 execution and exit**.

Master Orchestration titles Sequence 11 **“PM6 MT5 Execution & Exit Engine”**.
That is a *sequence title*, not a package name. **PM6** in this repository is
`pm6_post_trade` (Sequence 08). This package is **not** named `pm6`.

- Adapter (transport): `botmoduleproject1.adapters.mt5`
- Router + exit: this package
- Sequence 07 `Mt5BrokerAdapter` stays blocked
- Tickets: `DEMO-*` — not broker truth
- Live account kind: refused
- Entry code must not import the gateway; use `DemoRouter` after PM4 ALLOW

See `docs/MODULE_NUMBERING_MAP.md`.
