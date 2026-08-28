# Bootstrap governance

Status: Accepted for Sequence 02  
Date (UTC): 2026-08-28  
Trading readiness: **not ready**

This policy governs how configuration, secrets, feature flags, and preflight
interact with the PM1 kernel. It does not authorize trading.

## 1. Who may change configuration

| Profile | Who | How | Requires rebuild |
|---|---|---|---|
| `test` | Developer / CI | YAML overlay + test `environ=` | No |
| `backtest` | Researcher | YAML overlay + restart | No |
| `research` | Researcher | YAML overlay + restart | No |
| `demo` | Operator | YAML + prefixed env + restart | **No** |
| `live` | Nobody in this build | Recognized, then refused | N/A |

Demo configuration changes MUST be possible without rebuilding the package.
Change `configs/demo.example.yaml` (or a local non-secret overlay) and/or
`BOTMODULEPROJECT1_*` environment variables, then restart
`python -m botmoduleproject1 doctor --profile demo`.

Secrets never go in YAML. Secrets never go in git.

## 2. Source priority

Highest wins:

1. CLI / explicit init (`--profile`, `cli_mode`, test `extra=`)
2. `BOTMODULEPROJECT1_*` prefixed environment (nested with `__`)
3. Secret allowlist (`MT5_*`, `TELEGRAM_*`, `BOTMODULEPROJECT1_DATABASE_URL`)
4. Optional `--env-file` (allowlisted keys only)
5. YAML (`extends` parents merged first)
6. Code defaults (fail-closed)

Unprefixed ambient names (`DATABASE_URL`, `TRADING_MODE`, `LIVE_TRADING_ENABLED`,
`DEFAULT_SYMBOL`) are **ignored** so PaaS env cannot change posture.

## 3. Feature flags

Flags are typed (`FeatureFlagSpec`): name, description, default, allowed
profiles, safety classification.

| Safety | YAML may enable | Env opt-in | Default |
|---|---|---|---|
| `safe` | Yes | Yes | false |
| `requires-review` | Yes | Yes | false |
| `dangerous` | **No** — load fails | Required | false |

Dangerous flags currently: `enable_pm5_execution`, `enable_pm5_broker_adapter`,
`enable_mt5_demo_execution`, `enable_live_execution`, `enable_telegram_control`,
`enable_live_trading`. `enable_live_trading` has **no** override: env opt-in
still raises `LiveTradingDisabledError`.

Enabling a dangerous flag writes a `JournalEntry` with `EventType.CONFIG`.
That is the audit trail. Sequence 02 storage is an in-memory stub; PM8 will
persist the same contract.

## 4. Reproducible fingerprint

`Settings.fingerprint()` is SHA-256 of the **redacted** public dict, including
`profile` and resolved feature-flag names. Identical YAML + allowlisted env
⇒ identical fingerprint. A different symbol, profile, or flag ⇒ different
fingerprint. Secret *values* are not hashed; only present/absent.

## 5. Lifecycle (initialize → validate → connect → recover → run → shutdown)

Sequence 02 inserts `preflight_checked` into the PM1 machine rather than
forking a second one:

```text
created
  → config_loaded          # initialize
  → validated              # validate
  → preflight_checked      # python, files, secrets, deps, live-block, fs
  → registry_ready         # connect (stubs in Sequence 02)
  → wired
  → startup_checked
  → warmed
  → ready
  → running | degraded     # run (diagnostic only)
  → stopping → stopped     # shutdown
```

`live` cannot reach `running`. Missing required secrets fail at validate or
preflight, never half-wired.

Recovery completeness is still a future PM8 gate (`require_recovery: true`).
Until then the process may boot **DEGRADED** because the PM4 stub is not ready.

## 6. CLI

```text
python -m botmoduleproject1 --profile demo doctor --config configs/demo.example.yaml
python -m botmoduleproject1 live
```

Doctor/paper print `profile=` and `allowed_capabilities=`. `live` is recognized
and refused (exit 2 on Python 3.11+). Python < 3.11 fails first (exit 1, ADR-008).
