# Persistence recovery guide

Canonical Sequences 09–10. PM8 `PersistenceApiV1` is the only downstream data path. PM7 is the evidence journal (flag off → NullLedger).

Recovery order: restart drill → integrity → projection rebuild (isolated) → observe. Do not route before recovery. See `RB-RECOVERY-AFTER-RESTART` and `scripts/bot/emit_evidence.py`.
