# BOTMODULEPROJECT1 — SEQUENCE 02
# Configuration, Secrets & Bootstrap Governance

Ты — ведущий архитектор и implementation-orchestrator институциональной модульной Forex-системы для MT5 Demo.

Проект: BotModuleProject1. Репозиторий: GrokBuildapprepoFX.

ВАЖНО: у тебя нет доступа к внешним master-prompt файлам. Весь необходимый контекст приведён ниже целиком. Это единственный source-of-truth для текущего этапа.

## 0. Контекст предыдущих этапов (Sequence 00–01 — уже выполнены)

Уже создано и не должно быть удалено без необходимости:
- Полный architecture baseline, dependency graph, runtime modes, ADR-001..007 (docs/)
- PM1 kernel: bootstrap, settings, container, runtime, lifecycle, health, registry, contracts, capabilities, diagnostics, logging_config, exceptions, stubs (botmoduleproject1/app/)
- CLI entrypoint с режимами test/doctor/paper/live/backfill; live явно отключён (exit 2)
- Contracts v1 (schema_version 1.0.0): time, identity, market, session, signals, strategy (PM3-Strategy Engine), forecasting (PM3 QRF, отдельный namespace), risk, execution, journal, alerts, roles, tuning
- RiskGate protocol как эксклюзивный gate; NullRiskGate всегда DENY; OrderRequest требует risk_verdict_id
- 37 тестов, все проходят
- docs/prompts/PM1_Master_Prompt.md — сохранён полный текст прошлого промпта

## 1. Обязательное исправление перед продолжением (build gate condition)

В Sequence 01 обнаружено два отклонения, которые ОБЯЗАТЕЛЬНО нужно устранить в начале этого этапа, до перехода к новой функциональности:

1. **Python version mismatch.** Тесты запускались на CPython 3.10, хотя architecture baseline и ADR-001 требуют Python 3.11+. Зафиксируй точную минимальную версию в pyproject.toml (`requires-python = ">=3.11"`), добавь runtime-проверку версии Python при старте (fail-fast с понятным сообщением, если версия ниже 3.11), и явно проверь/задокументируй, на какой версии реально выполняются тесты в CI/локально. Если текущая среда разработки физически ограничена 3.10, зафиксируй это как явный, осознанный, документированный техдолг в docs/adr/ с отдельным ADR (ADR-008: Python version constraint and sandbox deviation), а не тихо игнорируй.

2. **Settings реализация.** В Sequence 01 Settings был реализован как `BaseModel` + explicit env overlay вместо полноценного `pydantic-settings.BaseSettings`. В этом этапе доведи Settings до полноценной pydantic-settings архитектуры, как изначально требовалось: множественные источники (env vars, .env, YAML config file), явный приоритет источников, SecretStr для чувствительных полей, при этом сохрани защиту от "ambient env pollution", которая была причиной прошлого отклонения — используй `pydantic-settings` с явным `env_prefix`, explicit `SettingsConfigDict`, и явную блокировку чтения нерелевантных env-переменных вне заданного prefix.

Не переходи к остальной части Sequence 02, пока эти два пункта не закрыты и не подтверждены тестами.

## 2. Non-negotiable safety rules (действуют на всех этапах проекта)

- Только MT5 Demo по умолчанию; live trading явно disabled.
- Ни один trade intent не может попасть в execution без положительного risk verdict.
- Никаких duplicate orders, silent retries, implicit parameter changes, неаудируемых действий.
- При stale data, broken connection, ledger inconsistency, model invalidity, config error или uncertain broker state — переход в safe halt/observe-only mode.
- Любое изменение архитектуры, контракта или risk policy сначала отражается в документации и тестах.
- Не переписывай код ради прохождения теста; исправляй первопричину.
- Не используй внешние данные, модели или зависимости без проверки совместимости, воспроизводимости и лицензирования.
- Секреты никогда не попадают в git, логи, тесты или документацию.

## 3. Цель Sequence 02

Создай безопасную конфигурационную систему с профилями Demo/Test/Backtest/Research, валидацией параметров, отсутствием hardcoded secrets, безопасными defaults, feature flags и startup preflight checks. Определи lifecycle: initialize → validate → connect → recover → run → shutdown.

## 4. Требуемые компоненты

### 4.1. Multi-profile configuration system

Реализуй профили конфигурации как явные, версионированные, валидируемые наборы:
- `demo` — единственный профиль, разрешающий сетевые операции с MT5 Demo-счётом.
- `test` — для unit/integration тестов, без реальных внешних соединений.
- `backtest` — исторические данные, без live-соединений, без записи в production ledger.
- `research` — расширенные диагностика/логирование, без исполнения ордеров.
- `live` — должен существовать как распознаваемое имя профиля, но с обязательной hard-блокировкой на уровне кода (не просто конфига), которая физически не позволяет runtime перейти в running state с этим профилем без отдельного будущего explicit override, которого сейчас не существует.

Каждый профиль должен:
- явно перечислять допустимые capabilities (market_data, risk_gating, execution и т.д.) и запрещённые для данного профиля операции;
- иметь собственный YAML template в configs/ (используй уже существующие base.example.yaml, demo.example.yaml, test.example.yaml, research.example.yaml как основу, добавь backtest.example.yaml);
- проходить строгую Pydantic-валидацию структуры и допустимых значений при загрузке.

### 4.2. Secrets governance

- Секреты живут исключительно в environment variables или `.env` (не в YAML, не в git).
- Все секретные поля — `SecretStr`, никогда не логируются и не попадают в diagnostics snapshot в открытом виде.
- Реализуй secret redaction helper, который используется во всех местах, где Settings объект может быть сериализован (logging, diagnostics, error messages).
- Добавь explicit validation: если обязательный секрет отсутствует для выбранного профиля (например, MT5 credentials для demo), startup должен fail-fast с понятной ошибкой без утечки значения.
- `.env.example` должен покрывать все возможные секретные поля с placeholder-значениями, без реальных данных.

### 4.3. Feature flags

- Реализуй типизированную feature flag систему (не просто bool в settings, а явная FeatureFlag модель с именем, описанием, default-значением, allowed profiles, и safety classification: safe / requires-review / dangerous).
- Все флаги, помеченные как dangerous, должны быть default-disabled и требовать явного opt-in через env, никогда через YAML defaults.
- Зарезервируй flags-заглушки для будущих модулей (например, `enable_pm4_risk_gate`, `enable_pm5_execution`, `enable_telegram_control`), все default false, так как эти модули ещё не реализованы.

### 4.4. Startup preflight checks

Реализуй явную preflight-фазу, которая выполняется до перехода lifecycle в `ready`:
- проверка версии Python (см. пункт 1);
- проверка обязательных конфигурационных файлов и их валидности;
- проверка наличия обязательных секретов для выбранного профиля;
- проверка совместимости зависимостей (сверка фактически установленных версий пакетов с requirements.txt/pyproject.toml);
- проверка, что live-профиль заблокирован, если он выбран;
- проверка filesystem permissions для каталогов логов/данных, если они уже определены архитектурой;
- агрегированный PreflightReport с списком passed/failed checks, который логируется и доступен через diagnostics.

Preflight должен быть частью lifecycle между `validated` и `registry_ready`, либо явно задокументирован как отдельная стадия, если текущая state machine требует уточнения — в этом случае явно опиши, куда preflight встраивается в существующий lifecycle из PM1, не создавая противоречий с уже реализованной state machine.

### 4.5. Bootstrap governance policy

Создай документ `docs/architecture/bootstrap_governance.md`, описывающий:
- кто/что может менять конфигурацию в каждом профиле;
- правило: изменение конфигурации в `demo` не должно требовать пересборки кода, только изменение YAML/env и restart;
- правило: любое изменение feature flag со статусом dangerous обязано быть зафиксировано в audit trail (используй существующий journal contract из Sequence 01: `JournalEntry`, `EventType`);
- правило: конфигурация должна быть воспроизводима — одинаковый набор env+yaml должен давать одинаковый config fingerprint (уже реализован в Sequence 01, используй его здесь и расширь для профилей).

## 5. Интеграция с уже существующим PM1 kernel

- Не переписывай Lifecycle, Registry, Container, Runtime с нуля — расширяй их для поддержки profiles, feature flags и preflight.
- Используй существующий `HealthCheckProvider` контракт для preflight checks там, где это уместно, вместо создания параллельной системы проверок.
- Используй существующий `diagnostics.py` для агрегации PreflightReport и расширенного config fingerprint per-profile.
- CLI должен получить возможность указывать профиль явно, например `python -m botmoduleproject1 --profile demo doctor`, и должен явно печатать выбранный профиль и его allowed capabilities при doctor/paper режимах.

## 6. Что запрещено на Sequence 02

Не реализовывать: торговые стратегии, индикаторы, trade intent generation, QRF/ML вычисления, risk calculations (кроме самой risk gate blocking-логики из Sequence 01, которую не трогаем), order sending, реальное MT5 соединение (можно оставить placeholder adapter), Telegram бота, database schema/migrations, реальные API вызовы, production deployment, любую форму live trading.

## 7. Тесты

Обязательное покрытие:
- загрузка и валидация каждого профиля (demo/test/backtest/research/live);
- явный тест, что live-профиль не может перевести runtime в running state;
- secret redaction (значения секретов никогда не появляются в snapshot/логах в тестах, проверяется строгим assert на отсутствие значения в сериализованном выводе);
- feature flag: dangerous flag default false, попытка включить без явного opt-in должна fail;
- preflight: успешный и неуспешный сценарии (например, отсутствующий обязательный секрет должен провалить preflight с понятной ошибкой);
- config fingerprint reproducibility: одинаковый вход → одинаковый fingerprint, разный вход → разный fingerprint;
- CLI: `--profile` флаг корректно передаётся и отражается в diagnostics output;
- регрессионный тест, что Python version guard действительно fail-fast на версии ниже 3.11 (можно через мокирование sys.version_info в тесте).

Никаких пустых тестов — только реальные тесты с полезными assertions.

## 8. Traceability requirement

Сохрани полный текст этого промпта в файл `docs/prompts/PM1_Sequence02_Configuration_Governance_Prompt.md`.

Обнови `docs/architecture/repository_assessment.md`, добавив секцию "Sequence 02 inputs", зафиксировав, что спецификация получена напрямую в промпте.

## 9. Обязательный итоговый отчёт

После завершения предоставь отчёт в Markdown:

1. Created/updated files: полный список с путями.
2. Gate-fix status: явное подтверждение исправления Python version mismatch и перехода Settings на полноценный pydantic-settings (или явное объяснение, если это оказалось невозможно, с ADR-008).
3. Profile system status: таблица профилей (demo/test/backtest/research/live) → COMPLETE/PARTIAL/BLOCKED, с описанием allowed capabilities для каждого.
4. Secrets governance status: подтверждение redaction, отсутствия секретов в git/логах.
5. Feature flags status: список реализованных флагов с safety classification.
6. Preflight status: список реализованных проверок.
7. Test results: сколько тестов, все ли проходят, разбивка по файлам.
8. Known risks and conflicts.
9. Build gate result: PASS / BLOCKED / NEEDS-DECISION.
10. Явное утверждение, что система НЕ готова для торговли, demo trading или production.
11. Точный следующий шаг: Sequence 03 — PM2 Market Data & Session Regime Engine.

Начни с исправления Python version mismatch и Settings-архитектуры (раздел 1), затем переходи к остальной части Sequence 02.
