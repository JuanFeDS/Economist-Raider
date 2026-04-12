# Data Model: Dashboard Principal de Indicadores Económicos

**Branch**: `001-main-dashboard` | **Date**: 2026-04-12

## Entidades del Dominio

### Indicator

Representa un indicador económico en un punto específico del tiempo.

```
Indicator
├── id: UUID
├── name: str                    # "IPC", "TRM", "Tasa de Referencia", etc.
├── category: IndicatorCategory  # MACROECONOMIC | MONETARY | LABOR | FISCAL
├── value: Decimal
├── unit: str                    # "%", "COP/USD", "puntos base", etc.
├── measured_at: date            # Fecha de la medición oficial
├── period_type: PeriodType      # DAILY | MONTHLY | QUARTERLY | ANNUAL
├── change_absolute: Decimal     # Variación vs período anterior
├── change_pct: Decimal          # Variación % vs período anterior
├── source_id: UUID              # FK → Source
├── is_quarantined: bool         # True si no pasó validación
├── quarantine_reason: str | None
└── created_at: datetime         # Timestamp de ingesta
```

**Invariantes**:
- `source_id` no puede ser nulo (Principio I)
- `measured_at` ≤ fecha actual
- `value` debe ser numérico finito
- Si `is_quarantined = True`, no debe exponerse en la UI principal

---

### Source

Fuente oficial de datos. Cada scraper corresponde a exactamente una Source.

```
Source
├── id: UUID
├── name: str               # "Banco de la República", "DANE", etc.
├── source_type: SourceType # OFFICIAL_GOV | CENTRAL_BANK | MEDIA
├── base_url: str           # URL base del organismo
├── last_successful_run: datetime | None
├── last_run_at: datetime | None
├── last_run_status: RunStatus  # SUCCESS | FAILED | RUNNING | NEVER
├── last_error: str | None
├── update_frequency: str   # "daily", "monthly", "quarterly"
└── is_active: bool
```

---

### Measurement

Medición individual dentro de una serie histórica. Normalizada por
separado de `Indicator` para optimizar queries de series temporales.

```
Measurement
├── id: UUID
├── indicator_name: str     # Nombre canónico del indicador
├── value: Decimal
├── unit: str
├── measured_at: date
├── source_id: UUID
└── created_at: datetime
```

---

### CollectionRun

Registro de cada ejecución del scheduler para una fuente.

```
CollectionRun
├── id: UUID
├── source_id: UUID
├── started_at: datetime
├── finished_at: datetime | None
├── status: RunStatus        # SUCCESS | FAILED | RUNNING
├── records_collected: int
├── records_quarantined: int
└── error_message: str | None
```

---

## Enums

```
IndicatorCategory: MACROECONOMIC | MONETARY | LABOR | FISCAL
PeriodType:        DAILY | MONTHLY | QUARTERLY | ANNUAL
SourceType:        OFFICIAL_GOV | CENTRAL_BANK | MEDIA
RunStatus:         SUCCESS | FAILED | RUNNING | NEVER
```

---

## Esquema SQLite

```sql
-- migrations/001_initial.sql

CREATE TABLE sources (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    base_url TEXT NOT NULL,
    last_successful_run TEXT,
    last_run_at TEXT,
    last_run_status TEXT NOT NULL DEFAULT 'NEVER',
    last_error TEXT,
    update_frequency TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE indicators (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    value TEXT NOT NULL,       -- Decimal stored as TEXT for precision
    unit TEXT NOT NULL,
    measured_at TEXT NOT NULL,
    period_type TEXT NOT NULL,
    change_absolute TEXT,
    change_pct TEXT,
    source_id TEXT NOT NULL REFERENCES sources(id),
    is_quarantined INTEGER NOT NULL DEFAULT 0,
    quarantine_reason TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE measurements (
    id TEXT PRIMARY KEY,
    indicator_name TEXT NOT NULL,
    value TEXT NOT NULL,
    unit TEXT NOT NULL,
    measured_at TEXT NOT NULL,
    source_id TEXT NOT NULL REFERENCES sources(id),
    created_at TEXT NOT NULL
);

CREATE TABLE collection_runs (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(id),
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL,
    records_collected INTEGER NOT NULL DEFAULT 0,
    records_quarantined INTEGER NOT NULL DEFAULT 0,
    error_message TEXT
);

-- Índices para queries frecuentes
CREATE INDEX idx_indicators_name ON indicators(name);
CREATE INDEX idx_indicators_measured_at ON indicators(measured_at DESC);
CREATE INDEX idx_measurements_name_date ON measurements(indicator_name, measured_at DESC);
CREATE INDEX idx_collection_runs_source ON collection_runs(source_id, started_at DESC);
```

---

## Relaciones

```
Source ──< CollectionRun   (una fuente tiene muchas ejecuciones)
Source ──< Indicator       (una fuente origina muchos indicadores)
Source ──< Measurement     (una fuente origina muchas mediciones)
Indicator                  (snapshot más reciente por indicador)
Measurement                (serie histórica — N registros por indicador)
```

---

## Indicadores iniciales

| Nombre canónico | Categoría | Fuente | Frecuencia | Unidad |
|----------------|-----------|--------|-----------|--------|
| IPC | MACROECONOMIC | DANE | Mensual | % variación |
| TRM | MONETARY | Banco de la República | Diaria | COP/USD |
| Tasa de Referencia | MONETARY | Banco de la República | Por reunión | % EA |
| Tasa de Desempleo | LABOR | DANE | Mensual | % |
| PIB Crecimiento | MACROECONOMIC | DANE | Trimestral | % variación |

---

## Reglas de validación

| Campo | Regla |
|-------|-------|
| IPC | Entre -5% y 50% mensual |
| TRM | Entre 1,000 y 10,000 COP/USD |
| Tasa de Referencia | Entre 0% y 30% EA |
| Tasa de Desempleo | Entre 0% y 50% |
| PIB Crecimiento | Entre -20% y 20% trimestral |
| Cualquier indicador | `measured_at` no puede ser futuro |
| Cualquier indicador | No se admiten duplicados (mismo nombre + measured_at) |
