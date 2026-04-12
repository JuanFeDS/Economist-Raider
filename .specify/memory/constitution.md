<!--
SYNC IMPACT REPORT
==================
Version change: (none) → 1.0.0
Added sections:
  - Core Principles (I–VI)
  - Stack & Constraints
  - Development Workflow
  - Governance
Templates reviewed:
  - .specify/templates/spec-template.md    ✅ compatible (no changes required)
  - .specify/templates/plan-template.md    ✅ compatible (no changes required)
  - .specify/templates/tasks-template.md   ✅ compatible (no changes required)
Deferred TODOs:
  - RATIFICATION_DATE set to first authoring date: 2026-04-11
  - Cloud deployment constraints TBD when deployment phase begins
-->

# Economist Raider Constitution

## Core Principles

### I. Fuente Confiable y Trazable (NON-NEGOTIABLE)

Toda pieza de información presentada en el observatorio DEBE estar vinculada
a su fuente original (URL, nombre del organismo, fecha de publicación).
Los datos sin fuente verificable NO DEBEN ser mostrados al usuario.
El sistema DEBE distinguir entre datos oficiales (gobierno, bancos centrales)
y datos de medios de comunicación, etiquetando el tipo de fuente siempre.

### II. Scraping Ético y Respetuoso

El sistema DEBE respetar el archivo `robots.txt` de cada sitio objetivo.
El sistema DEBE implementar rate-limiting con intervalos razonables entre
peticiones para no sobrecargar los servidores de origen.
Está PROHIBIDO evadir paywalls, CAPTCHAs de seguridad, o cualquier mecanismo
de acceso restringido. Solo se accede a contenido públicamente disponible.
El sistema DEBE identificarse honestamente mediante un User-Agent descriptivo.

### III. Clean Architecture

El sistema DEBE seguir Clean Architecture (Robert C. Martin). Las dependencias
SOLO apuntan hacia adentro — las capas externas conocen las internas, nunca
al revés:

- **Entities (Domain)**: modelos de negocio puros — Indicador, SerieHistórica,
  Fuente, EjecuciónRecolección. Sin dependencias externas.
- **Use Cases**: lógica de aplicación — ObtenerIndicadores, ActualizarFuente,
  ConsultarHistorial. Dependen solo del dominio.
- **Interface Adapters**: scrapers por fuente, repositorios, presentadores UI.
  Cada fuente de datos es un adapter independiente e intercambiable.
- **Frameworks & Drivers**: NiceGUI, SQLite, httpx, Playwright, APScheduler.
  Detalles de infraestructura confinados a la capa exterior.

Agregar una fuente nueva DEBE requerir únicamente un adapter nuevo.
Cambiar el motor de base de datos DEBE requerir únicamente cambiar el
repositorio. El dominio y los use cases NO DEBEN cambiar por decisiones
de infraestructura.

### IV. Actualización Periódica Automatizada

El sistema DEBE soportar actualizaciones programadas (schedulers) por fuente,
con frecuencias configurables según la naturaleza de cada dato
(ej: indicadores macroeconómicos diarios, noticias cada pocas horas).
Cada ejecución DEBE registrar en log: fuente, timestamp, registros obtenidos,
errores encontrados. El sistema DEBE ser resiliente: un fallo en una fuente
NO DEBE detener la actualización de las demás.

### V. Calidad y Validación de Datos

Los datos ingestados DEBEN pasar por una capa de validación antes de ser
almacenados o presentados. Esta capa DEBE verificar: formato, rangos
esperados, coherencia temporal y ausencia de duplicados.
Los datos que no superen validación DEBEN ser marcados como `cuarentenados`
y no presentados al usuario hasta revisión.
El sistema DEBE mantener historial de versiones de indicadores clave para
detectar correcciones retroactivas de fuentes oficiales.

### VI. UI Clara, Informativa y Escalable

La interfaz DEBE priorizar la comprensión rápida del estado económico sobre
la densidad de datos. Cada vista DEBE tener un propósito único y claro.
Los componentes de UI DEBEN ser reutilizables y desacoplados de la lógica
de negocio. La UI DEBE ser funcional en local sin configuración adicional,
y diseñada para ser desplegable en la nube sin refactoring mayor.

## Stack & Constraints

### Stack Tecnológico

- **Lenguaje principal**: Python 3.11+
- **Scraping / Ingesta**: `httpx` + `BeautifulSoup4` / `Playwright` para
  sitios con JS rendering
- **Procesamiento de datos**: `pandas` / `polars`
- **Almacenamiento local**: SQLite (structured data) + archivos JSON/CSV
  para exports
- **Scheduler**: `APScheduler` o `schedule`
- **UI**: `NiceGUI` — Python puro con HTML/CSS/Tailwind, corre sobre FastAPI
  internamente, funcional en local y desplegable en cloud sin cambios
- **Gráficas**: `Apache ECharts` vía `ui.echart()` de NiceGUI (soporte nativo,
  sin dependencias adicionales)
- **Testing**: `pytest` + `pytest-httpx` para mocks de red

### Restricciones Actuales

- El sistema DEBE funcionar completamente en local sin costos de
  infraestructura externa.
- NO se DEBEN usar servicios de pago (APIs de pago, cloud functions, etc.)
  en la fase local.
- El diseño DEBE permitir migración a despliegue cloud sin cambios
  arquitecturales mayores (12-factor app principles donde aplique).
- Las dependencias DEBEN ser gestionadas con `uv` o `pip` + `requirements.txt`
  con versiones pinadas.

### Fuentes de Datos Objetivo (iniciales)

- **Indicadores económicos**: DANE, Banco de la República de Colombia,
  Ministerio de Hacienda
- **Decisiones de gobierno**: sitios oficiales de ministerios, Diario Oficial
- **Medios**: portales de noticias económicas colombianos de acceso público
- **Contexto político**: fuentes de acceso público relevantes al impacto
  económico

## Development Workflow

- Todo módulo nuevo DEBE tener tests unitarios antes de integrarse.
- Los conectores de fuente DEBEN tener tests con fixtures (responses mockeadas)
  para evitar dependencia de red en CI.
- El código DEBE pasar linting (`ruff`) y formateo (`black` o `ruff format`)
  antes de cada commit.
- Las migraciones de esquema de base de datos DEBEN ser versionadas y
  reproducibles.
- La UI DEBE ser validada visualmente antes de marcar una feature como
  completada.

## Governance

Esta constitución rige todas las decisiones de arquitectura, scraping y
presentación del proyecto. Cualquier desviación de los principios aquí
definidos DEBE ser justificada explícitamente y documentada.

**Proceso de enmienda**:
1. Identificar el principio afectado y la justificación del cambio.
2. Incrementar la versión según semver (MAJOR: cambio de principio existente;
   MINOR: nuevo principio; PATCH: clarificación).
3. Actualizar `LAST_AMENDED_DATE` y el Sync Impact Report.

**Version**: 1.1.0 | **Ratified**: 2026-04-11 | **Last Amended**: 2026-04-12
