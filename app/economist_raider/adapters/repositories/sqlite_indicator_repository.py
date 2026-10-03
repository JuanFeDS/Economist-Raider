"""SQLite implementation of IndicatorRepository."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from economist_raider.domain.entities.historical_series import Measurement
from economist_raider.domain.entities.indicator import (
    Indicator,
    IndicatorCategory,
    PeriodType,
)
from economist_raider.domain.ports.indicator_repository import IndicatorRepository
from economist_raider.infrastructure.db import connection


class SQLiteIndicatorRepository(IndicatorRepository):

    def get_latest(self, indicator_name: str) -> Indicator | None:
        with connection.get_connection() as conn:
            row = conn.execute(
                """
                SELECT * FROM indicators
                WHERE name = ? AND is_quarantined = 0
                ORDER BY measured_at DESC
                LIMIT 1
                """,
                (indicator_name,),
            ).fetchone()
        return _row_to_indicator(row) if row else None

    def get_all_latest(self) -> list[Indicator]:
        with connection.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT i.* FROM indicators i
                INNER JOIN (
                    SELECT name, MAX(measured_at) AS max_date
                    FROM indicators
                    WHERE is_quarantined = 0
                    GROUP BY name
                ) latest ON i.name = latest.name AND i.measured_at = latest.max_date
                ORDER BY i.category, i.name
                """
            ).fetchall()
        return [_row_to_indicator(r) for r in rows]

    def save(self, indicator: Indicator) -> None:
        if self.exists(indicator.name, indicator.measured_at):
            return
        with connection.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO indicators (
                    id, name, category, value, unit, measured_at, period_type,
                    change_absolute, change_pct, source_id,
                    is_quarantined, quarantine_reason, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(indicator.id),
                    indicator.name,
                    indicator.category.value,
                    str(indicator.value),
                    indicator.unit,
                    indicator.measured_at.isoformat(),
                    indicator.period_type.value,
                    str(indicator.change_absolute) if indicator.change_absolute is not None else None,
                    str(indicator.change_pct) if indicator.change_pct is not None else None,
                    str(indicator.source_id),
                    int(indicator.is_quarantined),
                    indicator.quarantine_reason,
                    indicator.created_at.isoformat(),
                ),
            )
            conn.commit()
            # Also persist to measurements for historical series
            conn.execute(
                """
                INSERT OR IGNORE INTO measurements (
                    id, indicator_name, value, unit, measured_at, source_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid4()),
                    indicator.name,
                    str(indicator.value),
                    indicator.unit,
                    indicator.measured_at.isoformat(),
                    str(indicator.source_id),
                    indicator.created_at.isoformat(),
                ),
            )
            conn.commit()

    def get_history(
        self,
        indicator_name: str,
        from_date: date,
        to_date: date,
    ) -> list[Measurement]:
        with connection.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM measurements
                WHERE indicator_name = ?
                  AND measured_at BETWEEN ? AND ?
                ORDER BY measured_at ASC
                """,
                (
                    indicator_name,
                    from_date.isoformat(),
                    to_date.isoformat(),
                ),
            ).fetchall()
        return [_row_to_measurement(r) for r in rows]

    def exists(self, indicator_name: str, measured_at: date) -> bool:
        with connection.get_connection() as conn:
            row = conn.execute(
                "SELECT 1 FROM indicators WHERE name = ? AND measured_at = ? LIMIT 1",
                (indicator_name, measured_at.isoformat()),
            ).fetchone()
        return row is not None


def _row_to_indicator(row: object) -> Indicator:
    return Indicator(
        id=UUID(row["id"]),
        name=row["name"],
        category=IndicatorCategory(row["category"]),
        value=Decimal(row["value"]),
        unit=row["unit"],
        measured_at=date.fromisoformat(row["measured_at"]),
        period_type=PeriodType(row["period_type"]),
        change_absolute=Decimal(row["change_absolute"]) if row["change_absolute"] else None,
        change_pct=Decimal(row["change_pct"]) if row["change_pct"] else None,
        source_id=UUID(row["source_id"]),
        is_quarantined=bool(row["is_quarantined"]),
        quarantine_reason=row["quarantine_reason"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def _row_to_measurement(row: object) -> Measurement:
    return Measurement(
        id=UUID(row["id"]),
        indicator_name=row["indicator_name"],
        value=Decimal(row["value"]),
        unit=row["unit"],
        measured_at=date.fromisoformat(row["measured_at"]),
        source_id=UUID(row["source_id"]),
        created_at=datetime.fromisoformat(row["created_at"]),
    )
