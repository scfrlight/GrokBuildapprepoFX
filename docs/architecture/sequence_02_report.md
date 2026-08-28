# Sequence 02 Report — Configuration, Secrets & Bootstrap Governance

Date (UTC): 2026-08-28  
Project: BotModuleProject1  
Git: `scfrlight/GrokBuildapprepoFX`

## 1. Gate-fix status

| Deviation (Sequence 01) | Resolution | Status |
|---|---|---|
| Tests ran on CPython 3.10 while target is 3.11+ | `requires-python = ">=3.11"` kept; `assert_python_version()` fail-fast; ADR-008 documents sandbox 3.10.21 + missing 3.11 pip | COMPLETE |
| Settings was `BaseModel` + manual overlay | `Settings(BaseSettings)` with `SettingsConfigDict(env_prefix=BOTMODULEPROJECT1_)`, explicit source tuple, no default `os.environ` scan | COMPLETE |

## 2. Profile system

| Profile | Status | Allowed capabilities | Notes |
|---|---|---|---|
| demo | COMPLETE | platform, diagnostics, telemetry, market_data, risk_gating, storage, notifications | Only profile that may later use MT5 Demo network. Orders still forbidden. |
| test | COMPLETE | platform, diagnostics, telemetry | No real external connections. |
| backtest | COMPLETE | platform, diagnostics, telemetry, market_data, storage | No live network, no production ledger. |
| research | COMPLETE | platform, diagnostics, telemetry, forecasting | No execution. |
| live | COMPLETE / BLOCKED | platform, diagnostics, telemetry | Recognized. Load refused. Runtime cannot reach `running`. |

## 3. Secrets

- Secret fields are `SecretStr`.
- Allowlist only; unprefixed `DATABASE_URL` is not read (PaaS pollution).
- `public_dict()`, diagnostics, and fingerprint use `redact_node`.
- Enabled adapter without a secret fails at Settings validation and again at preflight.
- `.env.example` is placeholders only. No `.env` is stored in the workspace.

## 4. Feature flags

| Flag | Safety | Default |
|---|---|---|
| enable_pm2_market_data | requires-review | false |
| enable_strategy_engine | requires-review | false |
| enable_forecasting | requires-review | false |
| enable_pm4_risk_gate | requires-review | false |
| enable_pm5_execution | dangerous | false, env-only |
| enable_telegram_control | dangerous | false, env-only |
| enable_fine_tune_studio | requires-review | false |
| enable_live_trading | dangerous | false; opt-in still refused |

Dangerous YAML=true fails. Env opt-in writes `JournalEntry` `EventType.CONFIG`.

## 5. Preflight checks

`python.version`, `config.file`, `profile.live_blocked`, `secrets.required`, `dependencies.pinned`, `filesystem.permissions`, `profile.capabilities`.

Lifecycle: `validated` → **`preflight_checked`** → `registry_ready`.

## 6. Tests

**67 collected, 67 passed.**

See `tests/unit/` and `tests/contract/`. Live CLI still exits 2 when the Python guard is satisfied. On this sandbox’s real 3.10 interpreter, CLI exits 1 on the version guard first (ADR-008).

## 7. Build gate

**PASS.** Not a trading authorization.

## 8. Next step

**Sequence 03 — PM2 Market Data & Session Regime Engine.**
