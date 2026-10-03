# Implementation Plan: Dashboard Principal de Indicadores Económicos

**Branch**: `001-main-dashboard` | **Date**: 2026-04-12 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/001-main-dashboard/spec.md`

## Summary

Dashboard local que consume datos de fuentes oficiales colombianas (DANE,
Banco de la República, Ministerio de Hacienda) y los presenta mediante
tarjetas de indicadores con tendencia histórica. Arquitectura Clean con
capas Entities → Use Cases → Adapters → Infrastructure. UI construida con
NiceGUI + Apache ECharts. Actualización automática vía APScheduler.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: NiceGUI 1.x, httpx, BeautifulSoup4, Playwright,
pandas, APScheduler 3.x, pydantic v2
**Storage**: SQLite (local, sin servidor)
**Testing**: pytest + pytest-httpx (mocks de red) + pytest-anyio
**Target Platform**: Desktop local (Windows/Mac/Linux); cloud-deployable sin
cambios arquitecturales
**Project Type**: Web app local (NiceGUI levanta servidor FastAPI interno)
**Performance Goals**: Dashboard visible en < 5s desde arranque; gráfica
histórica renderizada en < 1s tras selección
**Constraints**: Sin costos de infraestructura; funcional offline para
consulta; datos actualizados con acceso a internet
**Scale/Scope**: 1 usuario local; 5+ indicadores iniciales; 24 meses de
historial por indicador

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Estado | Evidencia |
|-----------|--------|-----------|
| I. Fuente Confiable y Trazable | ✅ PASS | Entidad `Source` obligatoria en cada `Indicator`; FR-004 requiere URL de origen |
| II. Scraping Ético | ✅ PASS | `BaseScraper` debe verificar robots.txt, rate-limit y User-Agent honesto |
| III. Clean Architecture | ✅ PASS | Estructura de 4 capas; dependencias apuntan solo hacia adentro |
| IV. Actualización Periódica | ✅ PASS | APScheduler por fuente; fallo aislado (FR resilience) |
| V. Calidad y Validación | ✅ PASS | Capa de validación en `processors`; datos inválidos en cuarentena |
| VI. UI Clara y Escalable | ✅ PASS | NiceGUI + ECharts; componentes desacoplados de use cases |

**Resultado**: ✅ Todos los gates pasan. Se puede continuar.

## Project Structure

### Documentation (this feature)

```text
specs/001-main-dashboard/
├── plan.md              # Este archivo
├── research.md          # Phase 0 — decisiones técnicas
├── data-model.md        # Phase 1 — entidades y relaciones
├── quickstart.md        # Phase 1 — arrancar el proyecto
├── contracts/           # Phase 1 — interfaces/puertos
│   ├── repository_ports.md
│   └── scraper_contract.md
└── tasks.md             # Phase 2 — /speckit-tasks (pendiente)
```

### Source Code (repository root)

```text
economist_raider/
├── domain/
│   ├── entities/
│   │   ├── indicator.py          # Entidad Indicador
│   │   ├── historical_series.py  # Serie de mediciones
│   │   ├── source.py             # Fuente oficial
│   │   └── collection_run.py     # Registro de ejecución
│   └── ports/                    # Interfaces abstractas (inward boundary)
│       ├── indicator_repository.py
│       └── source_repository.py
│
├── application/
│   └── use_cases/
│       ├── get_current_indicators.py
│       ├── get_indicator_history.py
│       ├── update_source_data.py
│       └── get_collection_status.py
│
├── adapters/
│   ├── scrapers/
│   │   ├── base_scraper.py       # Contrato + robots.txt + rate-limit
│   │   ├── dane_scraper.py
│   │   ├── banrep_scraper.py
│   │   └── minhacienda_scraper.py
│   ├── repositories/
│   │   ├── sqlite_indicator_repository.py
│   │   └── sqlite_source_repository.py
│   └── presenters/
│       └── dashboard_presenter.py
│
├── infrastructure/
│   ├── db/
│   │   ├── connection.py
│   │   └── migrations/
│   │       └── 001_initial.sql
│   ├── scheduler/
│   │   └── job_scheduler.py
│   └── ui/
│       ├── app.py                # Punto de entrada NiceGUI
│       ├── pages/
│       │   └── dashboard.py
│       └── components/
│           ├── indicator_card.py
│           └── history_chart.py
│
├── tests/
│   ├── unit/
│   │   ├── domain/
│   │   └── application/
│   └── integration/
│       └── adapters/
│           └── scrapers/         # Tests con fixtures HTTP mockeados
│
├── main.py                       # Entry point
└── requirements.txt
```

**Structure Decision**: Monolito modular siguiendo Clean Architecture. Una
sola aplicación Python con capas explícitas. El servidor web es levantado
internamente por NiceGUI/FastAPI — no hay frontend separado. Esta estructura
es cloud-deployable directamente con un `Dockerfile` sin refactoring.

## Complexity Tracking

> No hay violaciones a la constitución. Tabla no aplica.
