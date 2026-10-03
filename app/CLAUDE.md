# Economist Raider — Development Guidelines

Auto-generated from feature plans + constitution. Last updated: 2026-04-12

## Project

Observatorio económico-político de Colombia. Extrae datos de fuentes
oficiales (DANE, Banco de la República, Ministerio de Hacienda) y los
presenta en un dashboard con indicadores y tendencias históricas.

## Architecture

Clean Architecture — dependencias apuntan SOLO hacia adentro:

```
domain/ → application/ → adapters/ → infrastructure/
```

- `domain/`: entidades puras (Indicator, Source, Measurement, CollectionRun)
  y puertos abstractos (RepositoryPorts). Sin dependencias externas.
- `application/`: use cases. Solo dependen del dominio.
- `adapters/`: scrapers por fuente, repositorios SQLite, presentadores UI.
- `infrastructure/`: NiceGUI/UI, SQLite, APScheduler. Detalles confinados aquí.

## Active Technologies

- **Python 3.11+**
- **UI**: NiceGUI 1.x (levanta FastAPI internamente)
- **Gráficas**: Apache ECharts vía `ui.echart()`
- **Scraping**: httpx + BeautifulSoup4 / Playwright (JS rendering)
- **Validación**: pydantic v2
- **Storage**: SQLite (stdlib sqlite3, migraciones SQL versionadas)
- **Scheduler**: APScheduler 3.x BackgroundScheduler
- **Testing**: pytest + pytest-httpx

## Project Structure

```text
economist_raider/
├── domain/entities/      # Indicator, Source, Measurement, CollectionRun
├── domain/ports/         # Interfaces abstractas de repositorios
├── application/use_cases/
├── adapters/scrapers/    # Un archivo por fuente (dane, banrep, minhacienda)
├── adapters/repositories/
├── adapters/presenters/
├── infrastructure/db/
├── infrastructure/scheduler/
├── infrastructure/ui/
├── tests/unit/
├── tests/integration/
└── main.py
```

## Commands

```bash
python main.py              # Arrancar dashboard + scheduler
python main.py --init-db    # Inicializar/migrar base de datos
python main.py --collect    # Recolección manual de todas las fuentes
pytest                      # Todos los tests
pytest tests/unit/          # Solo unitarios (sin red)
ruff check .                # Linting
ruff format .               # Formateo
```

## Scraping Rules (NON-NEGOTIABLE)

- Verificar `robots.txt` ANTES de cualquier request
- Rate limiting mínimo de 1 segundo entre requests al mismo dominio
- User-Agent: `EconomistRaider/1.0 (+<repo-url>)`
- Nunca evadir paywalls ni CAPTCHAs
- Dato inválido → cuarentena (no excepción)

## Code Style

- Pydantic v2 para entidades del dominio
- Decimal (no float) para valores monetarios y porcentajes
- Fechas: `date` para mediciones, `datetime` para timestamps de sistema
- Tests de scrapers: siempre con fixtures HTTP mockeados (pytest-httpx)
- No dependencias de infraestructura en `domain/` ni `application/`

## Specs

- Constitution: `.specify/memory/constitution.md`
- Feature 001: `specs/001-main-dashboard/`

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
