# Repository Assessment — Sequence 00

Date (UTC): 2026-08-28  
Assessor: BotModuleProject1 architecture baseline

## 1. Repositories examined

| Location | State | Role |
|---|---|---|
| Grok App Builder `/workspace` | TanStack Start scaffold; no Python trading code | Preview host + this baseline |
| [scfrlight/GrokBuildapprepoFX](https://github.com/scfrlight/GrokBuildapprepoFX) | Empty private repo created 2026-08-28, description `Fxtrade` | Designated git home |
| [scfrlight/FXTGBOT](https://github.com/scfrlight/FXTGBOT) | Legacy V6/V7 scanner monolith | Reference only — do not copy structure |
| [scfrlight/V8-bot-Jules-1](https://github.com/scfrlight/V8-bot-Jules-1) | Audit notes + config fragment | Reference only |
| [scfrlight/ForexTG](https://github.com/scfrlight/ForexTG), [Forex-TG](https://github.com/scfrlight/Forex-TG) | Empty | Unused |
| Google Drive | No PM master prompts found | Gap |

## 2. Mandatory source files (Sequence 00)

Searched in `/workspace`, GitHub (user `scfrlight`), and Google Drive.

| Required file | Found |
|---|---|
| `Grok_Build_Master_Orchestration_Prompt.md` | No |
| `PM1_Master_Prompt.md` | No |
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
| `requirements.txt` | Not in this repo (legacy FXTGBOT has one) |
| `# PM1–PM9a Modular Forex Trading Bot — Installation & Setup Guide.md` | No |

**Impact:** Sequence 00 proceeds from the normalized module map embedded in the Sequence 00 prompt itself. Sequence 01 must reconcile if the original PM prompts are later added under `docs/prompts/`.

## 3. Current workspace (before Sequence 00 writes)

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

## 4. Legacy FXTGBOT (do not import as the architecture)

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

## 5. Files that must never enter git

- `.env`, `.env.local`, any file matching `*.pem`, `*.key`
- `.venv/`, `__pycache__/`, caches, coverage
- `logs/`, `data/local/`, `data/cache/`, `artifacts/`
- Local DB files (`*.sqlite`, `*.db`)
- MT5 terminal data (`*.hcc`, `*.ex5` user copies, `terminal.ini` with accounts)
- Generated scans, ledgers, model binaries unless explicitly versioned in a registry path
- `node_modules/`

## 6. Requirements assessment (legacy vs target)

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
| Python version | Legacy README says 3.10+; target is **3.11+** for `tomllib`, `utc`, typing |
| Missing for target architecture | pydantic-settings, PyYAML, structlog, sqlalchemy/asyncpg (later), alembic (later), tenacity, orjson, pytest-asyncio, ruff, mypy |
| Do not carry forward by default | flask dashboard, yfinance, fake-useragent, textblob, vader, feedparser, pandas_ta (revisit in PM2/PM3) |

New `requirements.txt` in this repo is a **bootstrap set only** (config, typing, tests, logging). No MT5, no Telegram bot SDK, no ML stack until the owning sequence.

## 7. Conflicts to watch

1. **PM3 naming:** `PM3_Master_Prompt.md` is forecasting; “PM3-Strategy Engine” is a different module. Packages are `pm3_forecasting` vs `pm3_strategy_engine`.
2. **PM8 vs PM8a:** spec vs runtime. Only `pm8_persistence` is a package.
3. **`app/` path:** nested under `botmoduleproject1/app` to avoid web-bundler `app/` convention.
4. **Auth/DB in App Builder:** remain OFF. Do not reuse `src/lib/db.ts` for the trading ledger.
5. **Legacy user id in FXTGBOT `.env.example`:** treat as a hygiene defect; placeholders only here.
