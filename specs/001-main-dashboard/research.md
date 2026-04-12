# Research: Dashboard Principal de Indicadores Económicos

**Branch**: `001-main-dashboard` | **Date**: 2026-04-12

## Decisiones Técnicas

### 1. Framework de UI

**Decision**: NiceGUI 1.x
**Rationale**: Python puro, levanta FastAPI internamente, soporte nativo de
Apache ECharts vía `ui.echart()`, Tailwind CSS incluido, sin build steps.
Funcional en local y desplegable en cloud con la misma base de código.
**Alternatives considered**:
- Streamlit: descartado por el usuario (no permite control real de HTML/CSS)
- Dash (Plotly): más orientado a ciencia de datos, menos flexible en UI
- FastAPI + Jinja2: requiere escribir HTML/CSS a mano, más fricción inicial

### 2. Gráficas

**Decision**: Apache ECharts vía `ui.echart()` de NiceGUI
**Rationale**: Soporte nativo en NiceGUI sin dependencias adicionales.
ECharts es maduro, altamente configurable, soporta series temporales,
zoom interactivo y tooltips ricos — ideal para un observatorio.
**Alternatives considered**:
- Plotly: requiere Dash o conversión a HTML; más pesado
- Matplotlib: no interactivo en web

### 3. HTTP Client para scraping

**Decision**: `httpx` (sync mode para scrapers simples)
**Rationale**: API moderna compatible con requests, soporte async cuando
sea necesario, compatible con `pytest-httpx` para mocks en tests.
**Alternatives considered**:
- requests: sin soporte async nativo; peor para futuros scrapers concurrentes
- aiohttp: más complejo para uso sync/async mixto

### 4. Parser HTML

**Decision**: `BeautifulSoup4` + `lxml` como parser
**Rationale**: Estándar de facto, documentación abundante, suficiente para
páginas HTML estáticas de fuentes oficiales.
**Playwright** como alternativa para fuentes que requieran JS rendering
(se activa por fuente, no globalmente).
**Alternatives considered**:
- Scrapy: overkill para esta escala; añade complejidad de framework
- Selenium: más lento y pesado que Playwright

### 5. Validación de entidades

**Decision**: `pydantic v2`
**Rationale**: Validación declarativa, serialización JSON nativa, integración
natural con FastAPI/NiceGUI. Permite modelar invariantes del dominio
directamente en las entidades.
**Alternatives considered**:
- dataclasses + validación manual: más código boilerplate, propenso a errores
- attrs: menos ecosistema que pydantic

### 6. Almacenamiento

**Decision**: SQLite vía `sqlite3` (stdlib) con migraciones SQL versionadas
**Rationale**: Sin servidor, sin costo, suficiente para series temporales
de indicadores económicos (cientos de miles de registros máximo).
Migraciones en SQL puro para portabilidad futura a PostgreSQL.
**Alternatives considered**:
- PostgreSQL: innecesario para uso local de un usuario
- DuckDB: excelente para analytics pero no necesario a esta escala
- CSV/JSON: sin soporte de queries eficientes para series temporales

### 7. Scheduler

**Decision**: `APScheduler 3.x` con `BackgroundScheduler`
**Rationale**: Permite schedules por fuente con frecuencias distintas
(diaria, semanal, mensual), gestión de jobs en runtime, persistencia
opcional de jobs. Más robusto que `schedule` para casos de uso complejos.
**Alternatives considered**:
- `schedule`: más simple pero sin soporte de múltiples frecuencias
  independientes por job ni manejo de errores integrado
- Celery: excesivo para uso local sin broker

### 8. Fuentes de datos — accesibilidad pública

**Decision**: Scraping HTML + APIs REST donde estén disponibles

| Fuente | Método | Endpoint / URL | Indicadores |
|--------|--------|---------------|-------------|
| Banco de la República | API REST pública | `https://www.banrep.gov.co/es/estadisticas` + endpoints de series | TRM, Tasa de interés |
| DANE | Archivos CSV/XLSX + HTML | `https://www.dane.gov.co` | IPC, Desempleo, PIB |
| Ministerio de Hacienda | HTML / PDF parsing | `https://www.minhacienda.gov.co` | Indicadores fiscales |

**Rationale**: Las fuentes oficiales colombianas publican datos en formatos
accesibles sin autenticación. El Banco de la República tiene endpoints REST
documentados. DANE publica archivos descargables.

### 9. Arquitectura de dependencias

**Decision**: Clean Architecture con inyección de dependencias manual
(sin framework DI)
**Rationale**: Para esta escala, la composición manual en `main.py` es
suficiente y más legible. Se instancian repositorios concretos, se pasan
a use cases, se conecta con la UI.
**Alternatives considered**:
- dependency-injector: añade complejidad sin beneficio real a esta escala

## Resolución de NEEDS CLARIFICATION

No hubo markers de NEEDS CLARIFICATION en la spec. Todos los aspectos
ambiguos fueron resueltos con defaults razonables documentados en Assumptions.

## Riesgos identificados

| Riesgo | Probabilidad | Mitigación |
|--------|-------------|------------|
| DANE cambia formato de archivos | Media | Versionar fixtures de tests; alertas en scraper |
| Banrep cambia estructura HTML | Media | Tests de integración con snapshots |
| Indicador sin datos recientes | Alta | Mostrar último valor + fecha + advertencia (ya en spec) |
| JS rendering requerido en fuente | Baja | Playwright ya contemplado como fallback |
