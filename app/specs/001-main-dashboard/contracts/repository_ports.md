# Repository Ports (Interfaces)

**Branch**: `001-main-dashboard` | **Date**: 2026-04-12

Estos son los puertos (interfaces abstractas) que definen el límite entre
Use Cases y la capa de persistencia. Los Use Cases dependen de estas
interfaces — nunca de las implementaciones concretas (SQLite, etc.).

---

## IndicatorRepository

```python
class IndicatorRepository(ABC):

    @abstractmethod
    def get_latest(self, indicator_name: str) -> Indicator | None:
        """Retorna el indicador más reciente para un nombre dado."""

    @abstractmethod
    def get_all_latest(self) -> list[Indicator]:
        """Retorna el último valor de cada indicador activo."""

    @abstractmethod
    def save(self, indicator: Indicator) -> None:
        """Persiste un indicador. Lanza DuplicateError si ya existe."""

    @abstractmethod
    def get_history(
        self,
        indicator_name: str,
        from_date: date,
        to_date: date
    ) -> list[Measurement]:
        """Retorna la serie histórica de mediciones en el rango dado."""

    @abstractmethod
    def exists(self, indicator_name: str, measured_at: date) -> bool:
        """Verifica si ya existe una medición para evitar duplicados."""
```

---

## SourceRepository

```python
class SourceRepository(ABC):

    @abstractmethod
    def get_all_active(self) -> list[Source]:
        """Retorna todas las fuentes activas para el scheduler."""

    @abstractmethod
    def get_by_id(self, source_id: UUID) -> Source | None:

    @abstractmethod
    def update_run_status(
        self,
        source_id: UUID,
        status: RunStatus,
        error: str | None = None
    ) -> None:
        """Actualiza el estado de la última ejecución de una fuente."""

    @abstractmethod
    def save_collection_run(self, run: CollectionRun) -> None:
        """Registra el resultado de una ejecución de recolección."""
```

---

## Errores del dominio

```python
class DomainError(Exception): ...
class DuplicateMeasurementError(DomainError): ...
class SourceNotFoundError(DomainError): ...
class ValidationError(DomainError): ...
class QuarantineError(DomainError): ...
```
