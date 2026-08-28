# BOTMODULEPROJECT1 — SEQUENCE 01
# Contract-First Domain Foundation + PM1 Platform Bootstrap Core

Ты — ведущий архитектор и implementation-orchestrator институциональной модульной Forex-системы для MT5 Demo.

Проект: BotModuleProject1. Репозиторий: GrokBuildapprepoFX.

ВАЖНО: у тебя нет доступа к внешним master-prompt файлам PM1–PM9a. Весь необходимый контекст для этого этапа приведён ниже целиком. Прочитай его полностью перед началом работы. Это единственный source-of-truth для текущего этапа.

## 0. Контекст предыдущего этапа (Sequence 00 — уже выполнен)

Уже создано и не должно быть удалено или переписано без необходимости:
- docs/architecture/architecture_baseline.md
- docs/architecture/dependency_graph.md
- docs/architecture/runtime_modes.md
- docs/architecture/repository_assessment.md
- docs/architecture/sequence_00_report.md
- docs/adr/ADR-001 … ADR-007
- .env.example, configs/base.example.yaml, demo.example.yaml, test.example.yaml, research.example.yaml
- пакет botmoduleproject1/ (app, contracts, domain, application, adapters, modules PM2–PM9 — только заглушки)
- pyproject.toml, requirements.txt, requirements-dev.txt
- tests/unit/test_package_import.py

Известные риски с прошлого этапа, которые нужно устранить сейчас:
1. Коллизия имён: пакеты pm3_strategy_engine и pm3_forecasting должны остаться раздельными и явно задокументированными как разные модули.
2. MetaTrader5 — опциональная зависимость только для Windows, не hard dependency.
3. Мастер-промпты не были физически положены в docs/prompts/ — сейчас это исправляется данным промптом: сохрани весь текст этого промпта целиком в docs/prompts/PM1_Master_Prompt.md для будущей прослеживаемости (traceability).

## 1. Non-negotiable safety rules (действуют на всех этапах проекта)

- Только MT5 Demo по умолчанию; live trading должен быть явно disabled.
- Ни один trade intent не может попасть в execution без положительного risk verdict (PM4).
- Никаких duplicate orders, silent retries, implicit parameter changes или неаудируемых действий.
- При stale data, broken connection, ledger inconsistency, model invalidity, config error или uncertain broker state — переход в safe halt/observe-only mode.
- Любое изменение архитектуры, контракта или risk policy сначала отражается в документации и тестах.
- Не переписывай код ради прохождения теста; исправляй первопричину.
- Не используй внешние данные, модели или зависимости без проверки совместимости, воспроизводимости и лицензирования.

## 2. Цель Sequence 01

Определи и реализуй общие schemas/enums/value objects для market data, sessions, regimes, signals, strategy intents, QRF outputs, risk decisions, orders, positions, executions, journal events, alerts, approvals, roles и tuning changes. Установи версионирование контрактов и единый UTC/timezone policy.

Одновременно реализуй PM1 — platform bootstrap / composition root, который эти контракты будет использовать.

## 3. PM1 — Platform Bootstrap & Integration Core (полная спецификация)

Ты строишь ТОЛЬКО первый фундаментальный модуль будущей модульной Forex-платформы, но так, чтобы он уже был интеграционным ядром для всей будущей системы.

Важно:
- НЕ строй strategy logic, risk logic, broker execution logic, ML модели или Telegram business features.
- Строй архитектурное ядро, которое позже чисто интегрирует все эти модули.
- Это production-grade системная архитектура, не toy script launcher.
- Результат должен быть implementation-ready, testable, extensible, safe-by-default.
- Кодовая база — чистая, типизированная, модульная, готовая для будущей MT5-based live-подобной (но пока demo) торговли.
- Целевая среда: Python 3.11+, Windows 11, локальная разработка сначала, продакшн — позже.
- Английский язык для всего кода, имён файлов, комментариев, docstrings, логов и технической документации.
- Не используй версионированные имена в файлах или классах (никаких v9, v10 и т.п.).
- Не генерируй фейковые модули бизнес-логики; где нужны будущие модули — используй contracts, stubs, mocks, adapters, registries и placeholders с явными extension points.

### PRIMARY GOAL

Построй platform bootstrap/integration модуль как центральный composition root будущей торговой системы.

Модуль должен:
1. Загружать и валидировать конфигурацию.
2. Собирать зависимости в одном месте.
3. Определять строгие контракты для будущих модулей.
4. Регистрировать и управлять будущими pluggable модулями.
5. Выполнять startup/readiness/liveness проверки.
6. Предоставлять управление runtime lifecycle state.
7. Поддерживать test/demo/live-style режимы на архитектурном уровне.
8. Быть способным интегрировать все будущие модули позже без крупных переписываний.

### АРХИТЕКТУРНЫЕ ПРИНЦИПЫ

1. Composition Root — одно центральное место собирает всё приложение. Core logic и adapters не собирают себя сами. Только application assembly layer знает обо всех реализациях.
2. Dependency Injection — явная constructor injection и/или легковесный DI-контейнер. Создание зависимостей централизовано. Система поддерживает замену реализаций для тестов и будущих сред.
3. Typed Contracts — будущие модули представлены через Protocols и/или abstract base contracts. Определи контракты для будущей системы даже если реализаций пока нет.
4. Integration-First Design — строй для будущей интероперабельности. Модуль управляет регистрацией, совместимостью, lifecycle и health будущих модулей.
5. Fail-Fast Safety — invalid config, missing secrets, invalid dependency graph или failed critical readiness checks должны останавливать запуск до начала runtime.
6. Health Semantics — раздельные startup checks, readiness checks и liveness checks. Не сворачивай все health concerns в один boolean.
7. Observability — structured logging, startup diagnostics, configuration fingerprinting, environment metadata, module registry status, lifecycle transitions обязательны.
8. Testability — всё тестируется с mocks/stubs без реального MT5, реальной БД или внешних сервисов.

### ОЖИДАЕМАЯ СТРУКТУРА ПРОЕКТА

Интегрируй с уже существующим пакетом botmoduleproject1/ из Sequence 00. Расширь его следующими элементами внутри app/:

- app/__init__.py
- app/bootstrap.py
- app/settings.py
- app/container.py
- app/runtime.py
- app/lifecycle.py
- app/health.py
- app/registry.py
- app/contracts.py
- app/capabilities.py
- app/diagnostics.py
- app/logging_config.py
- app/exceptions.py

- interfaces/ (можно отдельно от app/, если контракты разрастутся)
- adapters/ — только placeholders или mock-safe adapters, никакой реальной торговой execution логики
- cli/entrypoint.py
- tests/ — unit, integration-style startup, contract, config validation, registry/lifecycle тесты
- configs/ — используй уже существующие example-файлы
- scripts/ — Windows start script, опциональный diagnostic script
- README.md — обнови существующий

### ОБЯЗАТЕЛЬНЫЕ CORE-КОМПОНЕНТЫ

**1. Settings Layer**
Сильная типизированная конфигурационная система на pydantic-settings.
- Одна центральная Settings модель, с nested models где уместно.
- Поддержка загрузки из environment variables, .env, и опционально config file.
- SecretStr для чувствительных значений.
- Строгая валидация обязательных полей.
- Поля: app mode, environment, logging level, paths, diagnostics settings, plugin/module loading policy, health-check behavior, future broker settings placeholder, future storage settings placeholder, future model registry settings placeholder, future notification settings placeholder.
- Config fingerprint/hash generation для аудита.
- Явная startup-валидация с человекочитаемыми ошибками.

**2. Contracts для будущих модулей**
Определи типизированные контракты (Protocol) минимум для:
- MarketDataProvider
- SignalProvider
- ModelProvider
- RiskProvider / RiskGate
- ExecutionProvider
- StorageProvider
- NotificationProvider
- MonitoringProvider
- ModuleMetadataProvider
- HealthCheckProvider

Каждый контракт должен быть осмысленно спроектирован, даже если методы минимальны. Включи metadata и capability exposure где уместно.

**3. Capability Model**
Определи систему capabilities для будущих модулей:
- market_data, signals, forecasting, risk_gating, execution, storage, notifications, telemetry, diagnostics

Каждая регистрация модуля должна декларировать: module name, module version, supported capabilities, compatibility/api version, is critical, dependencies on other module categories, health support, readiness requirement, liveness requirement.

**4. Module Registry**
- Регистрирует модули, отклоняет дубли.
- Валидирует metadata и зависимости между модулями.
- Lookup по contract/capability/name.
- Registry snapshots для диагностики.
- Поддержка plugin-style discovery или manual registration.
- Поддержка disabled modules и allowlists/denylists из конфига.

**5. Dependency Container**
Строит settings, конфигурирует logging, создаёт registry, создаёт diagnostics services, wiring lifecycle manager, регистрирует built-in mock/default реализации при необходимости, допускает dependency overrides в тестах, чисто разделяет application assembly от domain contracts.

**6. Lifecycle State Machine**
Явные lifecycle states: created → config_loaded → validated → registry_ready → wired → startup_checked → warmed → ready → running → degraded → stopping → stopped → failed.

- Transitions явные и валидируемые; invalid transitions вызывают понятные exceptions.
- Transitions логируются.
- Lifecycle manager класс.
- Graceful shutdown и failure transition.

**7. Health System**
Раздельные startup checks, readiness checks, liveness checks.
- Health result models.
- Критичные/некритичные checks.
- Агрегация результатов с детальным объяснением failing checks.
- Простое подключение health checks будущими модулями.
- Readiness fails при недоступности критичных зависимостей.
- Liveness отражает, жив ли runtime.
- Startup гейтит первый запуск.

**8. Runtime Orchestrator**
- Получает assembled dependencies.
- Запускает startup sequence.
- Входит в ready/running state.
- No-op main loop или simulated heartbeat loop.
- Graceful shutdown, diagnostic mode, self-test mode.
- НЕ исполняет торговые операции.

Этот runtime — будущая оболочка, в которую позже подключатся все реальные модули.

**9. Logging and Diagnostics**
- Централизованный logging config, консистентный logger naming.
- Startup banner/log block: app name, environment, mode, config fingerprint, loaded modules, lifecycle state.
- Diagnostics snapshot object.
- Человекочитаемое и машиночитаемое startup summary.
- Exception mapping для startup failures.

**10. CLI Entry Point**
- Режимы: test, doctor, paper, live, backfill.
- Override config path.
- Diagnostic flags.
- Без бизнес-логики в CLI — только вызов bootstrap layer.
- Режим live должен быть распознаваемым, но disabled-by-default с безопасной ошибкой.

**11. Windows Startup Script**
- Активирует окружение (или документирует ожидаемое), запускает CLI, поддерживает передачу mode/config аргументов, пишет логи в разумное место.

**12. Tests**
Обязательное покрытие: settings validation, fingerprint generation, registry duplicate prevention, dependency graph validation, capability registration, lifecycle transition validation, startup health aggregation, fail-fast boot behavior, dependency override behavior, CLI smoke test, runtime boot в diagnostic/self-test mode.

Никаких фейковых пустых тестов — только реальные тесты с полезными assertions.

### ДИЗАЙН-РЕШЕНИЯ

- Ясность важнее фреймворковой сложности.
- Модульно и институционально, не переинженерено ради стиля.
- Dataclasses и Pydantic models где уместно.
- Protocol / TypedDict / Enum / Literal где полезно.
- Никакой скрытой магии, никаких circular imports, никаких god classes.
- Никакой hard-coded broker логики.
- Никаких реальных MT5 API вызовов, кроме безобидного placeholder adapter.
- Никакой реальной отправки ордеров.
- Никакой реальной стратегии или ML реализации.
- Этот модуль — только system assembly и integration kernel.

## 4. Contract-First Domain Foundation (общие контракты для всей системы)

Дополнительно к PM1 создай пакет contracts/ (или domain/contracts/) с версионированными schemas/enums/value objects для:

- Market data: OHLCV bar, tick, timeframe enum, symbol metadata.
- Session/regime: SessionContext, RegimeState, RegimeType enum.
- Signals: SignalEvent, ConfluenceScore.
- Strategy intents: TradeIntent, ExitPlan, Direction enum, EntryType enum, ConsensusDecision enum, NoTradeDecision.
- QRF/forecast outputs: ForecastOutput, QuantileSet, ModelVersionInfo.
- Risk decisions: RiskVerdict, RiskRejectionReason enum, ExposureSnapshot.
- Orders/positions/executions: OrderRequest, OrderStatus enum, Position, ExecutionReport, ReconciliationRecord.
- Journal events: JournalEntry, EventType enum.
- Alerts/approvals: AlertEvent, AlertSeverity enum, ApprovalRequest, ApprovalStatus enum.
- Roles: OperatorRole enum, PermissionScope.
- Tuning changes: TuningChangeRequest, TuningChangeStatus enum, ParameterSchema (name, display_name, group, type, default, min/max, step, allowed_values, ui_mode, description, warning_text, requires_revalidation).

Требования к контрактам:
- Версионирование через явное поле schema_version или module suffix (contracts/v1/).
- Единая UTC-first time policy: только timezone-aware datetime, ISO-8601 сериализация, никаких naive datetime.
- Каждое межмодульное событие должно поддерживать event_id, correlation_id, causation_id и, где применимо, idempotency_key.
- Контракты реализуются как Pydantic models или frozen dataclasses с валидацией.
- Никакой бизнес-логики внутри контрактов — только структура данных и валидация формы.
- PM3-Strategy Engine (стратегии) и PM3 forecasting (QRF) должны использовать явно разные namespace для своих специфичных контрактов, чтобы не повторить коллизию имён из Sequence 00.

## 5. Traceability requirement

Сохрани полный текст этого промпта в файл docs/prompts/PM1_Master_Prompt.md — это единственный способ восстановить source-of-truth, так как внешние файлы недоступны агенту.

Обнови docs/architecture/repository_assessment.md, добавив секцию "Sequence 01 inputs", где зафиксируй, что PM1 spec и Contract-First Domain Foundation были получены напрямую в промпте, а не из внешнего файла.

## 6. Что запрещено на Sequence 01

Не реализовывать: торговые стратегии, индикаторы, trade intent generation логику (только контракт/структуру), QRF/ML вычисления, risk calculations, order sending, реальное MT5 соединение, Telegram бота, database schema/migrations, реальные API вызовы, production deployment, любую форму live trading.

## 7. Обязательный итоговый отчёт

После завершения предоставь отчёт в Markdown:

1. Created/updated files: полный список с путями.
2. PM1 components status: таблица (Settings, Contracts, Capability Model, Registry, Container, Lifecycle, Health, Runtime, Logging, CLI, Windows script, Tests) → COMPLETE / PARTIAL / BLOCKED.
3. Contract-First Domain Foundation status: список созданных contract-модулей и их версия.
4. Test results: сколько тестов, все ли проходят.
5. Known risks and conflicts: особенно PM3 naming collision, MT5 optional dependency, любые несоответствия с Sequence 00.
6. Build gate result: PASS / BLOCKED / NEEDS-DECISION.
7. Не утверждай, что система готова для торговли, demo trading или production.
8. Точный следующий шаг: Sequence 02 — Configuration, Secrets & Bootstrap Governance.

Начни с изучения текущей структуры репозитория botmoduleproject1/, затем приступай к реализации PM1 и Contract-First Domain Foundation.
