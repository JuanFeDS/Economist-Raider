# Scraper Contract

**Branch**: `001-main-dashboard` | **Date**: 2026-04-12

Contrato que todo scraper (adapter) DEBE cumplir para integrarse con
el sistema. Cada fuente de datos es un adapter independiente que implementa
`BaseScraper`.

---

## Interfaz

```python
class BaseScraper(ABC):

    source_name: str           # Nombre canónico de la fuente
    base_url: str              # URL base del sitio
    user_agent: str            # User-Agent honesto del observatorio
    rate_limit_seconds: float  # Mínimo de segundos entre requests (≥ 1.0)

    @abstractmethod
    def fetch(self) -> list[Indicator]:
        """
        Conecta a la fuente, extrae y retorna indicadores validados.

        - DEBE respetar robots.txt antes de hacer el primer request
        - DEBE esperar rate_limit_seconds entre requests consecutivos
        - DEBE retornar solo indicadores que pasen validación básica
        - Los indicadores que no pasen validación DEBEN ser retornados
          con is_quarantined=True y quarantine_reason poblado
        - NUNCA debe lanzar excepción por dato inválido individual;
          solo lanza si la fuente es completamente inalcanzable
        """

    def check_robots(self, url: str) -> bool:
        """
        Verifica si el scraping está permitido por robots.txt.
        Implementación base provista en BaseScraper.
        Retorna False si no está permitido (el scraper NO debe proceder).
        """

    def validate(self, indicator: Indicator) -> tuple[bool, str | None]:
        """
        Valida un indicador contra las reglas del data model.
        Retorna (True, None) si válido o (False, reason) si inválido.
        Implementación base provista — los scrapers pueden sobreescribir.
        """
```

---

## Reglas obligatorias para todo scraper

1. **robots.txt PRIMERO**: Antes de cualquier request, verificar
   `check_robots()`. Si retorna False, lanzar `RobotsDisallowedError`.

2. **Rate limiting**: Esperar `rate_limit_seconds` (mínimo 1.0) entre
   requests al mismo dominio.

3. **User-Agent**: Usar el `user_agent` de clase — nunca un UA que
   simule ser un navegador humano sin identificar al bot.

4. **Cuarentena, no excepción**: Un dato con formato inválido va a
   cuarentena. Solo se lanza excepción si el sitio es inalcanzable
   (timeout, 5xx, DNS failure).

5. **Idempotencia**: Llamar `fetch()` dos veces con los mismos datos
   publicados DEBE retornar los mismos indicadores.

---

## Ejemplo de implementación mínima

```python
class BanrepScraper(BaseScraper):
    source_name = "Banco de la República"
    base_url = "https://www.banrep.gov.co"
    user_agent = "EconomistRaider/1.0 (+https://github.com/user/economist_raider)"
    rate_limit_seconds = 2.0

    def fetch(self) -> list[Indicator]:
        if not self.check_robots(self.base_url):
            raise RobotsDisallowedError(self.base_url)
        # ... lógica de scraping ...
```

---

## Errores específicos de scrapers

```python
class ScraperError(Exception): ...
class RobotsDisallowedError(ScraperError): ...
class SourceUnreachableError(ScraperError): ...
class ParseError(ScraperError): ...
```
