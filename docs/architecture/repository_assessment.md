# Repository Assessment — Sequence 00 + Sequence 01

Date (UTC): 2026-08-28  
Assessor: BotModuleProject1 architecture baseline

## 1. Repositories examined

| Location | State | Role |
|---|---|---|
| Grok App Builder `/workspace` | TanStack Start scaffold + Sequence 01 kernel | Preview host + this baseline |
| [scfrlight/GrokBuildapprepoFX](https://github.com/scfrlight/GrokBuildapprepoFX) | Sequence 00 `002fdee`; Sequence 01 `b160932` | Designated git home |
| [scfrlight/FXTGBOT](https://github.com/scfrlight/FXTGBOT) | Legacy V6/V7 scanner monolith | Reference only — do not copy structure |
| [scfrlight/V8-bot-Jules-1](https://github.com/scfrlight/V8-bot-Jules-1) | Audit notes + config fragment | Reference only |
| [scfrlight/ForexTG](https://github.com/scfrlight/ForexTG), [Forex-TG](https://github.com/scfrlight/Forex-TG) | Empty | Unused |
| Google Drive | No PM master prompts found | Gap (partially closed in Sequence 01) |

## 2. Mandatory source files (Sequence 00)

Searched in `/workspace`, GitHub (user `scfrlight`), and Google Drive.

| Required file | Found |
|---|---|
| `Grok_Build_Master_Orchestration_Prompt.md` | No |
| `PM1_Master_Prompt.md` | **Yes — Sequence 01** (`docs/prompts/PM1_Master_Prompt.md`) |
| `PM2_Master_Prompt.md` | No |
| `PM3_Master_Prompt.md` | No |
| `PM3_Strategy_Engine_Master_Prompt.md` | No |
| `PM4_Master_Prompt.md` | No |
| `PM5_Master_Prompt.md` | No |
| `PM6_Master_Prompt.md` | No |
| `PM7_Master_Prompt.md` | No |
| `PM8_Master_Prompt.md` | No |
| `PM8a_Build_Spec.md` | No |
| `PM9_Operator_UX_Telegram_Control_Engine_Master_Prompt.md` | No |
| `PM9a_Strategy_Fine_Tune_Studio_Master_Prompt.md` | No |
| `requirements.txt` | Yes (this repo; bootstrap set) |
| `# PM1–PM9a Modular Forex Trading Bot — Installation & Setup Guide.md` | No |

**Impact:** Sequence 00 proceeded from the normalized module map embedded in the Sequence 00 prompt. Sequence 01 received the PM1 spec and Contract-First Domain Foundation **inline in the Sequence 01 prompt**, not as a pre-existing Drive/GitHub file. That inline spec is now persisted at `docs/prompts/PM1_Master_Prompt.md`.

## 3b. Sequence 02 inputs

Configuration, secrets, and bootstrap governance were **not** recovered from an external master-prompt file. They were supplied in full inside the Sequence 02 user prompt on 2026-08-28.

Traceability:

| Input | Source | Persisted as |
|---|---|---|
| Sequence 02 specification | Sequence 02 prompt (complete) | `docs/prompts/PM1_Sequence02_Configuration_Governance_Prompt.md` |
| Gate-fix: Python 3.11+ | Sequence 02 prompt, section 1.1 | ADR-008 + `python_version.py` |
| Gate-fix: pydantic-settings | Sequence 02 prompt, section 1.2 | `botmoduleproject1/app/settings.py` |
| Profiles / flags / preflight | Sequence 02 prompt, section 4 | `profiles.py`, `feature_flags.py`, `preflight.py`, `bootstrap_governance.md` |

No original PM2–PM9a files were present. Sequence 02 does not implement those modules.

## 3c. Sequence 03 inputs

PM2 Market Context Engine was **not** recovered from an external `PM2_Master_Prompt.md`.
It was supplied in full inside the Sequence 03 user prompt on 2026-08-28.

Traceability:

| Input | Source | Persisted as |
|---|---|---|
| PM2 Market Context Engine spec | Sequence 03 prompt (complete) | `docs/prompts/PM1_Sequence03_PM2_MarketContext_Prompt.md` |
| Feature flag `enable_pm2_market_data` | Sequence 02 catalog, narrowed in Sequence 03 | test + research env opt-in only |
| Output contracts | Sequence 03 section 10 | `botmoduleproject1/contracts/v1/pm2.py` |
| Folder structure | Sequence 03 section 15 | `botmoduleproject1/modules/pm2_market_context/` |

Original filename `PM2_Master_Prompt.md` was not found on Drive/GitHub. Sequence 03 treats the embedded spec as source of truth for this stage.

## 3d. Sequence 04 inputs

PM3-Strategy Engine was **not** recovered from an external `PM3_Strategy_Engine_Master_Prompt.md`.
It was supplied in full inside the Sequence 04 user prompt on 2026-08-28.

Traceability:

| Input | Source | Persisted as |
|---|---|---|
| PM3-Strategy Engine spec | Sequence 04 prompt (complete) | `docs/prompts/PM3_Strategy_Engine_Sequence04_Prompt.md` |
| Integration plan (pre-implementation) | Sequence 04 section 3 | `docs/architecture/pm3_strategy_engine_integration_plan.md` |
| Feature flag `enable_pm3_strategy_engine` | Sequence 02 catalog, renamed/narrowed | test + research env opt-in only |
| TradeIntent / consensus contracts | Sequence 04 sections 11–13 | `contracts/v1/strategy.py` + `strategy_engine.py` |

Original `PM3_Strategy_Engine_Master_Prompt.md` was not found on Drive/GitHub. Sequence 04 treats the embedded spec as source of truth. Forecasting/QRF remains a different module.

## 3e. Sequence 05 inputs

PM3 forecasting / QRF was **not** recovered from an external `PM3_Master_Prompt.md`.
It was supplied in full inside the Sequence 05 user prompt on 2026-08-28.

Traceability:

| Input | Source | Persisted as |
|---|---|---|
| PM3 forecasting / QRF spec | Sequence 05 prompt (complete) | `docs/prompts/PM3_Forecasting_Sequence05_Prompt.md` |
| Integration plan (pre-implementation) | Sequence 05 requirement | `docs/architecture/pm3_forecasting_integration_plan.md` |
| Feature flag `enable_forecasting` | Sequence 02 catalog, description updated | demo + test + research env opt-in; YAML false |
| ForecastOutput / QuantileSet | Sequence 01 contracts, extended | `contracts/v1/forecasting.py` |
| Estimator | Sequence 05: residual quantile envelope (not fitted QRF) | `modules/pm3_forecasting/inference/envelope.py` |

Original `PM3_Master_Prompt.md` was not found on Drive/GitHub. Sequence 05 treats the embedded spec as source of truth for this stage.

## 3. Sequence 01 inputs

PM1 specification and Contract-First Domain Foundation were **not** recovered from an external master-prompt file. They were supplied in full inside the Sequence 01 user prompt on 2026-08-28.

Traceability:

| Input | Source | Persisted as |
|---|---|---|
| PM1 Platform Bootstrap spec | Sequence 01 prompt, section 3 | `docs/prompts/PM1_Master_Prompt.md` |
| Contract-First Domain Foundation | Sequence 01 prompt, section 4 | same file, plus `botmoduleproject1/contracts/v1/` |
| Safety rules | Sequence 01 prompt, section 1 (same as Seq 00) | ADRs 001–007 (unchanged) |
| PM2–PM9a master prompts | still missing | `docs/prompts/README.md` |

No original `PM1_Master_Prompt.md` from Drive/GitHub was available to reconcile against. Sequence 01 therefore treats the embedded spec as the source of truth for this stage. Later sequences must reconcile if the original PM files appear.

## 4. Current workspace (before Sequence 00 writes)

Present (App Builder template, left intact):

- `package.json` / Vite / TanStack Start / Tailwind
- `src/lib/auth`, `src/lib/db.ts`, `src/lib/app-data` (unused; auth/db remain OFF)
- `scripts/*` platform helpers
- `server/middleware/grok-pwa.ts`
- `migrations/auth/0001_auth.sql` (platform; not used)
- `AGENTS.md`

Absent before Sequence 00:

- Python package, tests for the bot, configs, ADRs, `.gitignore` at project policy level, `.env.example`, `pyproject.toml`

No `.env` with secrets was present. No local databases or MT5 terminal files were present.

## 5. Legacy FXTGBOT (do not import as the architecture)

Observed traits that Sequence 00 explicitly rejects as the target shape:

- Multi-version monoliths (`forex_scanner_v1.py` … `v7.py`, filenames containing spaces)
- Telegram + scanner + execution in the same process/files (`telegram_trade_control.py`, `v7_ops.py`)
- JSON file ledgers and scan dumps (`latest_scan.json` ~282 KB committed)
- `MetaTrader5` as an unconditional requirement (Windows-only)
- `.env.example` containing a concrete Telegram user id — **must not be copied**
- Auto-execution path (`execution_mode: auto` + `--execute`) without an exclusive risk-gate module

Useful lessons retained as *principles*, not code:

- Separate secrets from JSON config
- Idempotency window for duplicate trades
- Drawdown guard and dry-run flag
- Health endpoint and doctor-style checks
- V8 audit: fail closed on costs, avoid M5 as a decision TF, purged CV for ML, correlation-aware heat

## 6. Files that must never enter git

- `.env`, `.env.local`, any file matching `*.pem`, `*.key`
- `.venv/`, `__pycache__/`, caches, coverage
- `logs/`, `data/local/`, `data/cache/`, `artifacts/`
- Local DB files (`*.sqlite`, `*.db`)
- MT5 terminal data (`*.hcc`, `*.ex5` user copies, `terminal.ini` with accounts)
- Generated scans, ledgers, model binaries unless explicitly versioned in a registry path
- `node_modules/`

## 7. Requirements assessment (legacy vs target)

Legacy FXTGBOT `requirements.txt`:

```text
MetaTrader5, pandas_ta, numpy, pandas, scikit-learn, requests,
beautifulsoup4, lxml, feedparser, vaderSentiment, python-dateutil,
fake-useragent, textblob, pytz, flask, yfinance, pytest>=8.0
```

| Topic | Assessment |
|---|---|
| Duplicates | None obvious; overlapping HTTP stack (`requests` vs future `httpx`) |
| Windows / MT5 | `MetaTrader5` **does not install on Linux**. Must be an extra, never a hard dependency in this sandbox |
| Python version | Legacy README says 3.10+; target is **3.11+** for `tomllib`, `utc`, typing. Sandbox pytest currently runs on 3.10.21 with a 3.11 interpreter present but without pip |
| Missing for target architecture | pydantic-settings, PyYAML, structlog, sqlalchemy/asyncpg (later), alembic (later), tenacity, orjson, pytest-asyncio, ruff, mypy |
| Do not carry forward by default | flask dashboard, yfinance, fake-useragent, textblob, vader, feedparser, pandas_ta (revisit in PM2/PM3) |

`requirements.txt` remains a **bootstrap set** (config, typing, tests, logging). No MT5, no Telegram bot SDK, no ML stack until the owning sequence.

## 8. Conflicts to watch

1. **PM3 naming:** `PM3_Master_Prompt.md` is forecasting; “PM3-Strategy Engine” is a different module. Packages are `pm3_forecasting` vs `pm3_strategy_engine`. Sequence 01 keeps separate contract namespaces (`contracts.v1.strategy` vs `contracts.v1.forecasting`) and separate stub modules.
2. **PM8 vs PM8a:** spec vs runtime. Only `pm8_persistence` is a package.
3. **`app/` path:** nested under `botmoduleproject1/app` to avoid web-bundler `app/` convention.
4. **Auth/DB in App Builder:** remain OFF. Do not reuse `src/lib/db.ts` for the trading ledger.
5. **Legacy user id in FXTGBOT `.env.example`:** treat as a hygiene defect; placeholders only here.
6. **Settings vs pydantic-settings:** Sequence 01 uses Pydantic `BaseModel` with explicit YAML + env overlay rather than `BaseSettings` auto-env, to avoid ambient env pollution. `pydantic-settings` remains a declared dependency for Sequence 02 governance.
7. **Readiness vs doctor boot:** `NullRiskGate` fails critical READINESS (fail-closed). Diagnostic boot uses `fail_on_critical=False` on readiness so `doctor` can still produce a DEGRADED snapshot. Orders remain impossible.
