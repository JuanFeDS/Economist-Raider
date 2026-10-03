# Tasks: Dashboard Principal de Indicadores Económicos

**Input**: Design documents from `specs/001-main-dashboard/`
**Branch**: `001-main-dashboard` | **Date**: 2026-04-12

**Organization**: Tasks grouped by user story — each story is independently
implementable and testable. No test tasks (not requested in spec).

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Parallelizable (archivos distintos, sin dependencias incompletas)
- **[Story]**: Historia de usuario a la que pertenece la tarea
- Paths relativos a la raíz del proyecto

---

## Phase 1: Setup

**Purpose**: Estructura del proyecto e inicialización

- [x] T001 Create full project directory structure per plan.md (domain/, application/, adapters/, infrastructure/, tests/)
- [x] T002 Create requirements.txt with all dependencies (nicegui, httpx, beautifulsoup4, lxml, playwright, pandas, pydantic, apscheduler, pytest, pytest-httpx, ruff)
- [x] T003 [P] Create pyproject.toml with ruff linting and formatting configuration
- [x] T004 [P] Create .env.example with PORT, SCHEDULE_* and LOG_LEVEL variables

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Dominio, persistencia y base de scrapers — DEBEN completarse antes de cualquier historia de usuario

**⚠️ CRÍTICO**: Ninguna historia de usuario puede comenzar hasta que esta fase esté completa

- [x] T005 Create database migration in infrastructure/db/migrations/001_initial.sql (sources, indicators, measurements, collection_runs tables + indexes)
- [x] T006 Implement SQLite connection manager in infrastructure/db/connection.py (singleton, migration runner on first connect)
- [x] T007 [P] Implement Indicator entity with pydantic v2 in domain/entities/indicator.py (IndicatorCategory, PeriodType enums, quarantine fields, invariants)
- [x] T008 [P] Implement Source entity with pydantic v2 in domain/entities/source.py (SourceType, RunStatus enums, is_active flag)
- [x] T009 [P] Implement Measurement entity in domain/entities/historical_series.py (value as Decimal, measured_at as date)
- [x] T010 [P] Implement CollectionRun entity in domain/entities/collection_run.py (started_at, finished_at, records_collected, records_quarantined)
- [x] T011 [P] Define IndicatorRepository abstract port in domain/ports/indicator_repository.py (get_latest, get_all_latest, save, get_history, exists)
- [x] T012 [P] Define SourceRepository abstract port in domain/ports/source_repository.py (get_all_active, get_by_id, update_run_status, save_collection_run)
- [x] T013 Implement SQLiteIndicatorRepository in adapters/repositories/sqlite_indicator_repository.py (implements IndicatorRepository port, uses connection.py)
- [x] T014 [P] Implement SQLiteSourceRepository in adapters/repositories/sqlite_source_repository.py (implements SourceRepository port)
- [x] T015 Implement BaseScraper in adapters/scrapers/base_scraper.py (robots.txt check, rate-limit ≥1s, honest User-Agent, quarantine on invalid data, ScraperError hierarchy)
- [x] T016 Create main.py entry point with CLI argument parsing (--init-db, --collect, --collect --source=name, --no-scheduler)

**Checkpoint**: Dominio completo, persistencia funcional, contrato de scrapers definido ✓

---

## Phase 3: User Story 1 — Vista de Indicadores en Tiempo Real (P1) 🎯 MVP

**Goal**: El usuario abre el dashboard y ve tarjetas con los 5 indicadores
clave (IPC, TRM, Tasa de Referencia, Desempleo, PIB) con valor actual,
variación y fecha de medición.

**Independent Test**: Ejecutar `python main.py --collect` seguido de
`python main.py` y verificar que aparecen 5 tarjetas con valores numéricos,
variación y fecha visible en `http://localhost:8080`

- [x] T017 [US1] Implement GetCurrentIndicators use case in application/use_cases/get_current_indicators.py (calls indicator_repository.get_all_latest(), filters quarantined)
- [x] T018 [P] [US1] Implement BanrepScraper in adapters/scrapers/banrep_scraper.py (TRM diaria + Tasa de Referencia, robots.txt check, rate_limit_seconds=2.0)
- [x] T019 [P] [US1] Implement DaneScraper in adapters/scrapers/dane_scraper.py (IPC mensual + Tasa de Desempleo mensual + PIB trimestral)
- [x] T020 [US1] Implement UpdateSourceData use case in application/use_cases/update_source_data.py (orchestrates scraper.fetch() → validate → save, handles quarantine, logs CollectionRun)
- [x] T021 [US1] Implement IndicatorCard NiceGUI component in infrastructure/ui/components/indicator_card.py (name, value+unit, change_absolute, change_pct, measured_at, category color coding)
- [x] T022 [US1] Implement dashboard page in infrastructure/ui/pages/dashboard.py (grid of IndicatorCards, calls GetCurrentIndicators use case, empty-state when no data)
- [x] T023 [US1] Wire up NiceGUI app in infrastructure/ui/app.py (register pages, configure title, port from env, serve dashboard.py)
- [x] T024 [US1] Compose dependencies in main.py (instantiate SQLite repos → inject into use cases → inject into UI → start scheduler if not --no-scheduler)

**Checkpoint**: MVP funcional — dashboard con 5 indicadores visible en local ✓

---

## Phase 4: User Story 2 — Tendencia Histórica de un Indicador (P2)

**Goal**: Al hacer clic en una tarjeta, el usuario ve una gráfica histórica
(Apache ECharts) con selector de rango 3/6/12 meses.

**Independent Test**: Clic en cualquier tarjeta de indicador → gráfica con
al menos 2 puntos de datos y selector de rango temporal funcionando.

- [x] T025 [US2] Implement GetIndicatorHistory use case in application/use_cases/get_indicator_history.py (calls indicator_repository.get_history(name, from_date, to_date))
- [x] T026 [US2] Implement HistoryChart NiceGUI component in infrastructure/ui/components/history_chart.py (ui.echart() with time-series line chart, tooltip with value+date, responsive)
- [x] T027 [US2] Add time range selector (3m / 6m / 12m toggle) to history view in infrastructure/ui/components/history_chart.py
- [x] T028 [US2] Add click handler on IndicatorCard to open history dialog in infrastructure/ui/pages/dashboard.py (passes indicator name to HistoryChart, handles no-data gracefully)

**Checkpoint**: Tendencia histórica funcionando desde cualquier tarjeta ✓

---

## Phase 5: User Story 3 — Trazabilidad de Fuentes (P3)

**Goal**: El usuario puede ver para cada indicador el organismo fuente y
acceder directamente al recurso de origen.

**Independent Test**: Clic en ícono de fuente en cualquier tarjeta → panel
con nombre del organismo y enlace clickeable al recurso original.

- [x] T029 [US3] Add source attribution section to IndicatorCard component in infrastructure/ui/components/indicator_card.py (source name badge, info icon)
- [x] T030 [US3] Implement SourceDetail component in infrastructure/ui/components/source_detail.py (source name, source_type label, base_url as clickable link, last_successful_run)
- [x] T031 [US3] Wire SourceDetail panel/dialog into dashboard page in infrastructure/ui/pages/dashboard.py (opens on info icon click, receives source_id, calls SourceRepository.get_by_id)

**Checkpoint**: Toda información tiene fuente verificable y enlace directo ✓

---

## Phase 6: User Story 4 — Estado de Actualización del Observatorio (P4)

**Goal**: El usuario ve cuándo fue la última actualización exitosa por fuente
y si hubo errores recientes.

**Independent Test**: Panel de estado muestra timestamp de última ejecución
exitosa y alerta visible cuando una fuente falló.

- [x] T032 [US4] Implement GetCollectionStatus use case in application/use_cases/get_collection_status.py (returns list of sources with last_run_status, last_successful_run, last_error)
- [x] T033 [US4] Implement APScheduler job scheduler in infrastructure/scheduler/job_scheduler.py (BackgroundScheduler, one job per active source, frequency from source.update_frequency, resilient — fallo individual no detiene los demás)
- [x] T034 [US4] Implement CollectionStatus NiceGUI component in infrastructure/ui/components/collection_status.py (table/list of sources, status badge SUCCESS/FAILED/RUNNING, last update timestamp, error tooltip)
- [x] T035 [US4] Integrate CollectionStatus panel into dashboard page in infrastructure/ui/pages/dashboard.py (footer or sidebar section, manual refresh button calls UpdateSourceData)

**Checkpoint**: Observatorio totalmente funcional con estado de salud visible ✓

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Completitud, robustez y calidad final

- [x] T036 [P] Implement MinHaciendaScraper stub in adapters/scrapers/minhacienda_scraper.py (estructura completa, fetch() lanza NotImplementedError con TODO, source registrada como inactive)
- [x] T037 [P] Implement DashboardPresenter in adapters/presenters/dashboard_presenter.py (formatea Decimal → string con separadores, colorea variaciones positivas/negativas, formatea fechas en español)
- [x] T038 [P] Add domain error classes to domain/errors.py (DomainError, DuplicateMeasurementError, SourceNotFoundError, ValidationError, QuarantineError, ScraperError hierarchy)
- [x] T039 Validate quickstart.md end-to-end: ejecutar todos los comandos documentados y confirmar que funcionan en entorno limpio

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Sin dependencias — comenzar de inmediato
- **Phase 2 (Foundational)**: Depende de Phase 1 — **bloquea todas las historias**
- **Phase 3 (US1)**: Depende de Phase 2 — es el MVP
- **Phase 4 (US2)**: Depende de Phase 2; se puede iniciar en paralelo con US1 tras Phase 2
- **Phase 5 (US3)**: Depende de Phase 2; independiente de US1 y US2
- **Phase 6 (US4)**: Depende de T020 (UpdateSourceData) de US1
- **Phase 7 (Polish)**: Depende de que las historias deseadas estén completas

### Dependencias entre tareas dentro de US1

```
T007–T010 (entidades) ──→ T011–T012 (puertos)
T011–T012             ──→ T013–T014 (repositorios)
T013–T014             ──→ T017 (GetCurrentIndicators)
T015 (BaseScraper)    ──→ T018, T019 (scrapers concretos)
T017 + T018 + T019    ──→ T020 (UpdateSourceData)
T017                  ──→ T021–T022 (UI cards + page)
T020 + T022 + T023    ──→ T024 (composición en main.py)
```

### Parallel Opportunities

```bash
# Phase 2 — ejecutar en paralelo:
T007 (Indicator entity) & T008 (Source entity) &
T009 (Measurement entity) & T010 (CollectionRun entity)

T011 (IndicatorRepository port) & T012 (SourceRepository port)

T013 (SQLiteIndicatorRepository) & T014 (SQLiteSourceRepository)

# Phase 3 — ejecutar en paralelo tras T015:
T018 (BanrepScraper) & T019 (DaneScraper)
```

---

## Parallel Example: Phase 2

```
Batch A (en paralelo):
  T007 domain/entities/indicator.py
  T008 domain/entities/source.py
  T009 domain/entities/historical_series.py
  T010 domain/entities/collection_run.py

Batch B (en paralelo, tras Batch A):
  T011 domain/ports/indicator_repository.py
  T012 domain/ports/source_repository.py

Batch C (en paralelo, tras Batch B):
  T013 adapters/repositories/sqlite_indicator_repository.py
  T014 adapters/repositories/sqlite_source_repository.py
```

---

## Implementation Strategy

### MVP (Solo User Story 1)

1. Completar Phase 1: Setup
2. Completar Phase 2: Foundational ← **crítico, bloquea todo**
3. Completar Phase 3: User Story 1
4. **VALIDAR**: `python main.py --collect && python main.py` → ver 5 indicadores
5. El observatorio ya entrega valor mínimo viable

### Entrega Incremental

1. Setup + Foundational → base lista
2. US1 → Dashboard con indicadores → **demo/uso real**
3. US2 → Tendencia histórica → mayor profundidad analítica
4. US3 → Trazabilidad → confianza total en los datos
5. US4 → Estado del observatorio → autonomía operativa

---

## Notes

- `[P]` = archivos distintos, sin dependencias sobre tareas incompletas
- Cada story es testeable de forma independiente (ver criterio en cada phase)
- Valores monetarios y porcentajes: usar `Decimal`, nunca `float`
- Scrapers: siempre verificar `robots.txt` antes de cualquier request (Principio II)
- Commit tras cada phase o grupo lógico (`/speckit-git-commit`)
