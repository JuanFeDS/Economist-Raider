"""SQLite implementation of SourceRepository."""

from datetime import datetime
from uuid import UUID

from economist_raider.domain.entities.collection_run import CollectionRun
from economist_raider.domain.entities.source import RunStatus, Source, SourceType
from economist_raider.domain.ports.source_repository import SourceRepository
from economist_raider.infrastructure.db import connection


class SQLiteSourceRepository(SourceRepository):

    def get_all_active(self) -> list[Source]:
        with connection.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM sources WHERE is_active = 1"
            ).fetchall()
        return [_row_to_source(r) for r in rows]

    def get_by_id(self, source_id: UUID) -> Source | None:
        with connection.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM sources WHERE id = ?", (str(source_id),)
            ).fetchone()
        return _row_to_source(row) if row else None

    def update_run_status(
        self,
        source_id: UUID,
        status: RunStatus,
        error: str | None = None,
    ) -> None:
        now = datetime.utcnow().isoformat()
        with connection.get_connection() as conn:
            if status == RunStatus.SUCCESS:
                conn.execute(
                    """
                    UPDATE sources
                    SET last_run_status = ?, last_run_at = ?,
                        last_successful_run = ?, last_error = NULL
                    WHERE id = ?
                    """,
                    (status.value, now, now, str(source_id)),
                )
            else:
                conn.execute(
                    """
                    UPDATE sources
                    SET last_run_status = ?, last_run_at = ?, last_error = ?
                    WHERE id = ?
                    """,
                    (status.value, now, error, str(source_id)),
                )
            conn.commit()

    def upsert(self, source: Source) -> None:
        with connection.get_connection() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO sources (
                    id, name, source_type, base_url, update_frequency, is_active
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(source.id),
                    source.name,
                    source.source_type.value,
                    source.base_url,
                    source.update_frequency,
                    int(source.is_active),
                ),
            )
            conn.commit()

    def save_collection_run(self, run: CollectionRun) -> None:
        with connection.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO collection_runs (
                    id, source_id, started_at, finished_at, status,
                    records_collected, records_quarantined, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(run.id),
                    str(run.source_id),
                    run.started_at.isoformat(),
                    run.finished_at.isoformat() if run.finished_at else None,
                    run.status.value,
                    run.records_collected,
                    run.records_quarantined,
                    run.error_message,
                ),
            )
            conn.commit()


def _row_to_source(row: object) -> Source:
    return Source(
        id=UUID(row["id"]),
        name=row["name"],
        source_type=SourceType(row["source_type"]),
        base_url=row["base_url"],
        last_successful_run=datetime.fromisoformat(row["last_successful_run"])
        if row["last_successful_run"]
        else None,
        last_run_at=datetime.fromisoformat(row["last_run_at"])
        if row["last_run_at"]
        else None,
        last_run_status=RunStatus(row["last_run_status"]),
        last_error=row["last_error"],
        update_frequency=row["update_frequency"],
        is_active=bool(row["is_active"]),
    )
