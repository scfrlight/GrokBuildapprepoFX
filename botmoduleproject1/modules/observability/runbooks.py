"""Sequence 14 runbooks. Markdown is generated from this catalog."""

from __future__ import annotations

from pathlib import Path

from botmoduleproject1.contracts.v1.observability import Runbook

_PROHIBITED_ALWAYS = (
    "Do not send live, paper, or real Demo orders.",
    "Do not bind Telegram Bot API.",
    "Do not bypass PM4.",
    "Do not treat SIM-* or DEMO-* as broker truth.",
    "Do not set trading_readiness=true.",
    "Do not start Sequence 15.",
)


def _rb(**kwargs: object) -> Runbook:
    prohibited = tuple(kwargs.get("prohibited_operator_actions") or ())  # type: ignore[arg-type]
    merged = tuple(dict.fromkeys(list(prohibited) + list(_PROHIBITED_ALWAYS)))
    kwargs["prohibited_operator_actions"] = merged
    return Runbook.model_validate(kwargs)


RUNBOOKS: tuple[Runbook, ...] = (
    _rb(runbook_id="RB-STARTUP-CLEAN", title="Clean startup", trigger="Operator starts doctor/test/observe on Python 3.11+ with default flags.", symptoms=("process banners NOT TRADE READY", "lifecycle degraded or ready-for-observe"), safety_classification="observe-only", automatic_system_behavior="Version guard, load settings, Null* binds, health probes, trading_readiness=false.", operator_inspection_commands=("python -m botmoduleproject1 doctor --profile test --config configs/test.example.yaml",), prohibited_operator_actions=("Do not pass --profile live.",), recovery_steps=("Fix Python/config if doctor exits non-zero.",), verification_steps=("doctor exits 0", "banner contains NOT TRADE READY"), rollback_steps=("Stop the process. No state to roll back.",), evidence_to_preserve=("doctor.out", "config fingerprint"), closure_criteria="Kernel assembled; live closed.", escalation_criteria="Startup fails after config is valid.", executable_check="doctor_exits_zero"),
    _rb(runbook_id="RB-SHUTDOWN-SAFE", title="Safe shutdown", trigger="Operator stops the process or runtime.stop() is called.", symptoms=("lifecycle STOPPING then STOPPED",), safety_classification="observe-only", automatic_system_behavior="No orders are flushed. Outbox is not force-drained onto a venue.", operator_inspection_commands=("python -m botmoduleproject1 doctor --profile test --config configs/test.example.yaml",), prohibited_operator_actions=("Do not SIGKILL to skip audit.",), recovery_steps=("Allow STOPPING→STOPPED.", "Restart with doctor."), verification_steps=("no broker send on shutdown",), rollback_steps=("N/A",), evidence_to_preserve=("runtime log",), closure_criteria="Process stopped; no live side effects.", escalation_criteria="Process hangs in STOPPING.", executable_check="runtime_stop"),
    _rb(runbook_id="RB-STALE-MARKET-DATA", title="Stale market data", trigger="Stale detector fires or last tick age exceeds threshold.", symptoms=("botmodule.market.stale_events increments", "operational_health=degraded"), safety_classification="safe-stop", automatic_system_behavior="Routing halted. trading_readiness remains false. Observe-only.", operator_inspection_commands=("python -m botmoduleproject1 observe --profile test --config configs/test.example.yaml --json",), prohibited_operator_actions=("Do not force a tick.", "Do not widen staleness to keep trading."), recovery_steps=("Wait for fresh data.", "Keep flags off."), verification_steps=("stale_data=true implies accept_trade=false",), rollback_steps=("N/A — safe-stop is the recovery.",), evidence_to_preserve=("observability snapshot",), closure_criteria="Stale flag cleared; still not trade-ready.", escalation_criteria="Stale persists across sessions.", executable_check="stale_forces_safe_stop"),
    _rb(runbook_id="RB-PERSISTENCE-UNAVAILABLE", title="Persistence unavailable", trigger="SQLite/API errors or NullStorage when writes are required.", symptoms=("persistence_readiness fail/degraded", "persistence.errors"), safety_classification="halt-writes", automatic_system_behavior="Refuse unjournaled writes. Not-ready for trade.", operator_inspection_commands=("python -m botmoduleproject1 observe --profile test --config configs/test.example.yaml --json",), prohibited_operator_actions=("Do not switch to an unversioned file drop.",), recovery_steps=("Inspect store path.", "Follow backup/restore if corruption."), verification_steps=("persistence dimension not PASS while flag off is expected DEGRADED",), rollback_steps=("Remain on NullStorage.",), evidence_to_preserve=("persistence error logs",), closure_criteria="Writes either journaled or refused.", escalation_criteria="Integrity also failing.", executable_check="persistence_dimension"),
    _rb(runbook_id="RB-LEDGER-INTEGRITY", title="Ledger integrity mismatch", trigger="Hash chain or checksum mismatch.", symptoms=("integrity_error", "ledger_compromised"), safety_classification="halt", automatic_system_behavior="No rewrite. Correction event only. trading halted.", operator_inspection_commands=("python scripts/bot/emit_evidence.py --out-dir docs/evidence",), prohibited_operator_actions=("Do not delete audit rows.", "Do not rehash the chain."), recovery_steps=("Preserve files.", "Escalate.", "Use correction events."), verification_steps=("committed rows unchanged",), rollback_steps=("Restore from verified backup only after checksum match.",), evidence_to_preserve=("ledger dump", "backup checksum"), closure_criteria="Mismatch documented; chain not rewritten.", escalation_criteria="Always escalate integrity failures.", executable_check="integrity_fail_not_ready"),
    _rb(runbook_id="RB-OUTBOX-BACKLOG", title="Outbox backlog", trigger="outbox.backlog gauge above threshold.", symptoms=("relay lag growing",), safety_classification="degraded", automatic_system_behavior="Do not drop. Do not send to a real venue.", operator_inspection_commands=("python -m botmoduleproject1 observe --profile test --config configs/test.example.yaml --json",), prohibited_operator_actions=("Do not purge the outbox to look green.",), recovery_steps=("Inspect consumers.", "Keep flags off."), verification_steps=("backlog metric exists in catalog",), rollback_steps=("N/A",), evidence_to_preserve=("outbox snapshot",), closure_criteria="Backlog explained; no venue send.", escalation_criteria="Dead-letter also growing.", executable_check="metric_catalog"),
    _rb(runbook_id="RB-DUPLICATE-CALLBACK", title="Duplicate callback", trigger="Same event_id or execution idempotency key replayed.", symptoms=("duplicate_event or duplicate_execution",), safety_classification="safe-ignore", automatic_system_behavior="First commit wins. Second ignored.", operator_inspection_commands=("python -m botmoduleproject1 observe --profile test --config configs/test.example.yaml --json",), prohibited_operator_actions=("Do not mint a new id to force a second apply.",), recovery_steps=("Confirm original record.",), verification_steps=("idempotency tests remain green",), rollback_steps=("N/A",), evidence_to_preserve=("idempotency key", "first record id"), closure_criteria="Single committed effect.", escalation_criteria="Two distinct commits for one key.", executable_check="duplicate_ignored"),
    _rb(runbook_id="RB-RECONCILIATION-DEGRADED", title="Reconciliation degraded", trigger="No venue, or mismatch vs SIM/DEMO tickets.", symptoms=("reconciliation.degraded_count", "broker_venue=unavailable"), safety_classification="degraded-not-pass", automatic_system_behavior="Status=degraded. Absence of venue never pass.", operator_inspection_commands=("python -m botmoduleproject1 observe --profile test --config configs/test.example.yaml --json",), prohibited_operator_actions=("Do not force reconciliation=pass.",), recovery_steps=("Leave degraded.", "Do not attach a real terminal."), verification_steps=("broker_venue is unavailable when flags off",), rollback_steps=("N/A",), evidence_to_preserve=("reconciliation record",), closure_criteria="Status is degraded or unavailable, never silent pass.", escalation_criteria="Mismatch against an expected simulation.", executable_check="venue_absent_not_pass"),
    _rb(runbook_id="RB-RECOVERY-AFTER-RESTART", title="Recovery after restart", trigger="Process restart. RestartDrill or orchestrator recovery.", symptoms=("reopen seq unchanged", "recovery_readiness"), safety_classification="recover-then-observe", automatic_system_behavior="Recovery before routing. trading_readiness=false.", operator_inspection_commands=("python scripts/bot/emit_evidence.py --out-dir docs/evidence",), prohibited_operator_actions=("Do not route before recovery completes.",), recovery_steps=("Run RestartDrill.", "Confirm sequence."), verification_steps=("restart_drill.log passed=True",), rollback_steps=("Stop if integrity invalid.",), evidence_to_preserve=("restart_drill.log",), closure_criteria="Reopen integrity valid; still not trade-ready.", escalation_criteria="Sequence moved or integrity invalid.", executable_check="restart_drill"),
    _rb(runbook_id="RB-BACKUP-VERIFICATION", title="Backup verification", trigger="Scheduled or manual backup().", symptoms=("backup_restore.log verified=True",), safety_classification="observe", automatic_system_behavior="Checksum is dump-specific (UUIDs/timestamps). Restore verifies against THAT dump.", operator_inspection_commands=("python scripts/bot/emit_evidence.py --out-dir docs/evidence",), prohibited_operator_actions=("Do not expect local and CI dump checksums to match.",), recovery_steps=("If verified=False, refuse restore.",), verification_steps=("runtime_untouched=True", "payload_canonical comparable"), rollback_steps=("Discard the bad file.",), evidence_to_preserve=("backup_restore.log", "dump checksum", "payload_canonical_sha256"), closure_criteria="File hashes to its own checksum.", escalation_criteria="Checksum mismatch on the same file.", executable_check="backup_restore"),
    _rb(runbook_id="RB-RESTORE-VERIFICATION", title="Restore verification", trigger="Operator asks to restore a backup file.", symptoms=("verify_file ok or MigrationError",), safety_classification="halt-on-mismatch", automatic_system_behavior="Mismatch raises. Live sequence not mutated.", operator_inspection_commands=("python scripts/bot/emit_evidence.py --out-dir docs/evidence",), prohibited_operator_actions=("Do not --force a checksum skip.",), recovery_steps=("Use a verified file only.",), verification_steps=("sequence_before == sequence_after_verify",), rollback_steps=("Keep live db; do not apply the bad dump.",), evidence_to_preserve=("restore_verifications row",), closure_criteria="Verified file or refused restore.", escalation_criteria="Live seq changed during verify.", executable_check="backup_restore"),
    _rb(runbook_id="RB-FAILED-MIGRATION", title="Failed migration", trigger="upgrade_to/rollback raises MigrationError.", symptoms=("schema version unchanged",), safety_classification="halt", automatic_system_behavior="Refuse v1 drop with a non-empty journal.", operator_inspection_commands=("python -m pytest tests/unit/test_pm8a_seq10.py --tb=short",), prohibited_operator_actions=("Do not DROP tables by hand.",), recovery_steps=("Stay on current version.", "Inspect MigrationError."), verification_steps=("tests refuse v1 drop",), rollback_steps=("rollback only 2→1 when allowed",), evidence_to_preserve=("migration log",), closure_criteria="Schema consistent; journal intact.", escalation_criteria="Partial DDL applied.", executable_check="migration_refuse_v1"),
    _rb(runbook_id="RB-FAILED-PROJECTION", title="Failed projection rebuild", trigger="projection rebuild throws or lags.", symptoms=("projection.lag", "projection_error"), safety_classification="isolated-rebuild", automatic_system_behavior="Do not rebuild on the live write connection if it can race.", operator_inspection_commands=("python -m botmoduleproject1 observe --profile test --config configs/test.example.yaml --json",), prohibited_operator_actions=("Do not delete the event log to speed rebuild.",), recovery_steps=("Rebuild in isolation.",), verification_steps=("metric catalog includes projection.lag",), rollback_steps=("Keep previous projection.",), evidence_to_preserve=("rebuild duration sample",), closure_criteria="Projection either rebuilt or explicitly stale.", escalation_criteria="Rebuild loops.", executable_check="metric_catalog"),
    _rb(runbook_id="RB-MT5-UNAVAILABLE", title="MT5 unavailable", trigger="No terminal, flag off, or adapter refused.", symptoms=("broker_venue=unavailable",), safety_classification="unavailable-not-pass", automatic_system_behavior="No real send. DEMO-* is not broker truth.", operator_inspection_commands=("python -m botmoduleproject1 observe --profile test --config configs/test.example.yaml --json",), prohibited_operator_actions=("Do not attach a real MT5 terminal.", "Do not enable mt5_demo_adapter in YAML."), recovery_steps=("Leave venue unavailable.",), verification_steps=("venue_present=false", "accept_trade=false"), rollback_steps=("N/A",), evidence_to_preserve=("observability snapshot",), closure_criteria="Venue unavailable documented.", escalation_criteria="Any attempt to open a live socket.", executable_check="venue_absent_not_pass"),
    _rb(runbook_id="RB-SIM-EXEC-REJECTION", title="Simulated execution rejection", trigger="SIM/DEMO engine rejects an intent.", symptoms=("broker_rejected public message",), safety_classification="simulation", automatic_system_behavior="Record rejection. Do not invent a fill.", operator_inspection_commands=("python -m pytest tests/unit/test_seq11_mt5_exit.py --tb=short",), prohibited_operator_actions=("Do not coerce SIM/DEMO to a venue ticket.",), recovery_steps=("Inspect PM4 verdict and simulation reason.",), verification_steps=("SIM-* / DEMO-* never broker truth tests green",), rollback_steps=("N/A",), evidence_to_preserve=("simulation receipt",), closure_criteria="Rejection recorded; no broker send.", escalation_criteria="A fill appears without a venue.", executable_check="sim_not_broker_truth"),
    _rb(runbook_id="RB-KILL-SWITCH", title="Kill-switch activation", trigger="Operator or risk kill-switch.", symptoms=("risk denials", "trading halted"), safety_classification="halt", automatic_system_behavior="No auto-rearm. No auto-promote.", operator_inspection_commands=("python -m botmoduleproject1 observe --profile test --config configs/test.example.yaml --json",), prohibited_operator_actions=("Do not auto-rearm.", "Do not weaken the switch."), recovery_steps=("Leave halted.", "Architect permission required to change policy."), verification_steps=("trading_readiness false",), rollback_steps=("N/A — halt stands.",), evidence_to_preserve=("kill-switch audit",), closure_criteria="Switch remains armed; no trading.", escalation_criteria="Any attempt to auto-rearm.", executable_check="trading_readiness_false"),
    _rb(runbook_id="RB-OPERATOR-PERMISSION-DENIAL", title="Operator permission denial", trigger="Command outside role/scope or HITL trying to skip PM4.", symptoms=("permission_denied", "denied_actions metric"), safety_classification="deny", automatic_system_behavior="Deny. Audit. HITL cannot skip PM4.", operator_inspection_commands=("python -m pytest tests/unit/test_pm4_safety.py tests/unit/test_pm8_hitl.py --tb=short",), prohibited_operator_actions=("Do not grant a shadow role.",), recovery_steps=("Re-issue a permitted observe command.",), verification_steps=("permission denied tests green",), rollback_steps=("N/A",), evidence_to_preserve=("command receipt",), closure_criteria="Denied command has an audit row.", escalation_criteria="A denied command still mutated risk.", executable_check="no_pm4_bypass"),
    _rb(runbook_id="RB-INCIDENT-ESCALATION", title="Incident escalation", trigger="Unresolved incident or integrity/secret event.", symptoms=("incidents.unresolved > 0",), safety_classification="escalate", automatic_system_behavior="Do not auto-close. Do not auto-promote.", operator_inspection_commands=("python -m botmoduleproject1 observe --profile test --config configs/test.example.yaml --json",), prohibited_operator_actions=("Do not close without evidence.",), recovery_steps=("Preserve evidence.", "Notify architect."), verification_steps=("incident metrics exist",), rollback_steps=("N/A",), evidence_to_preserve=("incident bundle",), closure_criteria="Escalation recorded.", escalation_criteria="This runbook IS the escalation.", executable_check="metric_catalog"),
    _rb(runbook_id="RB-SECRET-EXPOSURE", title="Secret exposure response", trigger="Secret value found in logs, evidence, or chat.", symptoms=("secret_handling_error",), safety_classification="critical", automatic_system_behavior="Redact. Fail export. Halt.", operator_inspection_commands=("python -m pytest tests/unit/test_seq14_observability.py::test_secret_redaction_in_log_metadata --tb=short",), prohibited_operator_actions=("Do not commit a rotation secret to git.",), recovery_steps=("Rotate credential.", "Purge leaked artifact.", "Re-run redaction tests."), verification_steps=("redaction tests fail if a known secret is injected",), rollback_steps=("Revert the leaking commit if already pushed.",), evidence_to_preserve=("redacted copy only",), closure_criteria="No secret value remains in git or evidence.", escalation_criteria="Always escalate exposures.", executable_check="redaction"),
    _rb(runbook_id="RB-CORRUPTED-EVIDENCE", title="Corrupted evidence package", trigger="Evidence checksum mismatch or secret in bundle.", symptoms=("verified=False", "redaction failure"), safety_classification="reject", automatic_system_behavior="Refuse the package. Do not fake a green checksum.", operator_inspection_commands=("python scripts/bot/emit_seq14_evidence.py --out-dir docs/evidence/seq14",), prohibited_operator_actions=("Do not recompute a matching checksum over mutated bytes.",), recovery_steps=("Regenerate from a clean run.",), verification_steps=("payload_canonical vs dump checksum distinction documented",), rollback_steps=("Keep the corrupt file as evidence of corruption, isolated.",), evidence_to_preserve=("bad checksum", "new clean bundle"), closure_criteria="Only clean bundles are linked from the audit.", escalation_criteria="Someone asks to 'just hash it again'.", executable_check="evidence_no_secrets"),
)

RUNBOOK_BY_ID = {rb.runbook_id: rb for rb in RUNBOOKS}

REQUIRED_RUNBOOK_COUNT = 20


def render_markdown(rb: Runbook) -> str:
    def bullets(items: tuple[str, ...]) -> str:
        return "\n".join(f"- {item}" for item in items)

    return f"""# {rb.runbook_id}: {rb.title}

Sequence 14 runbook. Observe-only. Not a trading procedure.

1. **Trigger.** {rb.trigger}
2. **Observable symptoms.**
{bullets(rb.symptoms)}
3. **Safety classification.** {rb.safety_classification}
4. **Automatic system behavior.** {rb.automatic_system_behavior}
5. **Operator inspection commands.**
{bullets(rb.operator_inspection_commands)}
6. **Prohibited operator actions.**
{bullets(rb.prohibited_operator_actions)}
7. **Recovery steps.**
{bullets(rb.recovery_steps)}
8. **Verification steps.**
{bullets(rb.verification_steps)}
9. **Rollback steps.**
{bullets(rb.rollback_steps)}
10. **Evidence to preserve.**
{bullets(rb.evidence_to_preserve)}
11. **Closure criteria.** {rb.closure_criteria}
12. **Escalation criteria.** {rb.escalation_criteria}

Executable check id: `{rb.executable_check}`
"""


def write_markdown(directory: Path) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for rb in RUNBOOKS:
        path = directory / f"{rb.runbook_id.lower()}.md"
        path.write_text(render_markdown(rb), encoding="utf-8")
        written.append(path)
    index = directory / "README.md"
    lines = [
        "# Sequence 14 runbooks",
        "",
        "Generated from `botmoduleproject1.modules.observability.runbooks`.",
        "",
        "- [pm8a_backup_restore.md](./pm8a_backup_restore.md) — Sequence 10 backup/restore (kept)",
        "",
    ]
    for rb in RUNBOOKS:
        lines.append(f"- [{rb.runbook_id}](./{rb.runbook_id.lower()}.md) — {rb.title}")
    index.write_text("\n".join(lines) + "\n", encoding="utf-8")
    written.append(index)
    return written
