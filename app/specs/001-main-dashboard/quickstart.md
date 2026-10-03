# Quickstart: Dashboard Principal

**Branch**: `001-main-dashboard` | **Date**: 2026-04-12

## Prerrequisitos

- Python 3.11+
- `uv` (recomendado) o `pip`
- Acceso a internet para la primera recolección de datos

## Instalación

```bash
# Clonar el repo
git clone <repo-url>
cd economist_raider

# Crear entorno virtual e instalar dependencias
uv venv
uv pip install -r requirements.txt

# (Alternativa con pip)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Primera ejecución

```bash
# 1. Inicializar la base de datos
python main.py --init-db

# 2. Recolectar datos por primera vez (requiere internet)
python main.py --collect

# 3. Arrancar el dashboard
python main.py
```

El dashboard estará disponible en `http://localhost:8080`

## Comandos disponibles

```bash
python main.py              # Arranca UI + scheduler automático
python main.py --init-db    # Crea/migra la base de datos local
python main.py --collect    # Recolección manual de todas las fuentes
python main.py --collect --source=banrep   # Recolectar solo una fuente
python main.py --no-scheduler              # UI sin actualizaciones automáticas
```

## Estructura de datos local

```
economist_raider/
└── data/
    └── economist_raider.db   # Base de datos SQLite (en .gitignore)
```

## Dependencias principales

```
nicegui>=1.4
httpx>=0.27
beautifulsoup4>=4.12
lxml>=5.0
playwright>=1.44
pandas>=2.2
pydantic>=2.7
apscheduler>=3.10
pytest>=8.0
pytest-httpx>=0.30
```

## Configuración (opcional)

Crea un archivo `.env` en la raíz (no se versiona):

```env
# Puerto del servidor (default: 8080)
PORT=8080

# Frecuencias de actualización (en horas)
SCHEDULE_TRM=24
SCHEDULE_IPC=720       # ~mensual
SCHEDULE_BANREP=168    # ~semanal

# Logging
LOG_LEVEL=INFO
```

## Tests

```bash
# Todos los tests
pytest

# Solo unitarios (sin red)
pytest tests/unit/

# Solo integración (con fixtures HTTP)
pytest tests/integration/

# Con cobertura
pytest --cov=economist_raider
```
