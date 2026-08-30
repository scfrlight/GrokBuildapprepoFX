"""Consolidated SQLite DDL for canonical Sequence 09 (schema v1) and Sequence 10 (v2)."""

from __future__ import annotations

SCHEMA_V1 = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    checksum TEXT NOT NULL,
    applied_at TEXT NOT NULL,
    direction TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    sequence_no INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL UNIQUE,
    correlation_id TEXT NOT NULL,
    causation_id TEXT,
    idempotency_key TEXT,
    occurred_at TEXT NOT NULL,
    event_type TEXT NOT NULL,
    producer TEXT NOT NULL,
    family TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    prev_hash TEXT NOT NULL,
    row_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS signals (
    signal_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    committed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    client_order_id TEXT NOT NULL UNIQUE,
    intent_id TEXT,
    verdict_id TEXT,
    state TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    committed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS executions (
    execution_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    venue_kind TEXT NOT NULL,
    venue_ticket TEXT,
    venue_callback_id TEXT,
    payload_json TEXT NOT NULL,
    committed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS positions_proj (
    symbol TEXT PRIMARY KEY,
    qty TEXT NOT NULL,
    avg_px TEXT NOT NULL,
    as_of TEXT NOT NULL,
    source_seq INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS idempotency_keys (
    edge TEXT NOT NULL,
    scope TEXT NOT NULL,
    key TEXT NOT NULL,
    result_ref TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (edge, scope, key)
);

CREATE TABLE IF NOT EXISTS outbox (
    outbox_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    topic TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    state TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    published_at TEXT
);

CREATE TABLE IF NOT EXISTS inbox (
    event_id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    state TEXT NOT NULL,
    processed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS recovery_checkpoints (
    checkpoint_id TEXT PRIMARY KEY,
    cursor_seq INTEGER NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS projections (
    name TEXT PRIMARY KEY,
    last_event_seq INTEGER NOT NULL,
    payload_json TEXT NOT NULL,
    rebuilt_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS recon_records (
    recon_id TEXT PRIMARY KEY,
    local_ref TEXT NOT NULL,
    venue_ref TEXT,
    state TEXT NOT NULL,
    detail_json TEXT NOT NULL,
    committed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    audit_id TEXT PRIMARY KEY,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    target TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    occurred_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS integrity_log (
    check_id TEXT PRIMARY KEY,
    state TEXT NOT NULL,
    detail_json TEXT NOT NULL,
    occurred_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS repair_log (
    repair_id TEXT PRIMARY KEY,
    check_id TEXT,
    action TEXT NOT NULL,
    new_event_id TEXT,
    detail_json TEXT NOT NULL,
    occurred_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS snapshots (
    snapshot_id TEXT PRIMARY KEY,
    scope TEXT NOT NULL,
    checksum TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS backup_manifest (
    backup_id TEXT PRIMARY KEY,
    path TEXT NOT NULL,
    checksum TEXT NOT NULL,
    event_count INTEGER NOT NULL,
    verified INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS export_packages (
    export_id TEXT PRIMARY KEY,
    checksum TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""

SCHEMA_V2_UP = """
CREATE TABLE IF NOT EXISTS backup_schedules (
    schedule_id TEXT PRIMARY KEY,
    cadence_seconds INTEGER NOT NULL,
    retain_count INTEGER NOT NULL,
    last_run_at TEXT,
    enabled INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS restore_verifications (
    verification_id TEXT PRIMARY KEY,
    backup_id TEXT NOT NULL,
    checksum_ok INTEGER NOT NULL,
    event_count INTEGER NOT NULL,
    verified_at TEXT NOT NULL,
    detail_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS restart_drills (
    drill_id TEXT PRIMARY KEY,
    passed INTEGER NOT NULL,
    log_json TEXT NOT NULL,
    ran_at TEXT NOT NULL
);
"""

SCHEMA_V2_DOWN = """
DROP TABLE IF EXISTS restart_drills;
DROP TABLE IF EXISTS restore_verifications;
DROP TABLE IF EXISTS backup_schedules;
"""
