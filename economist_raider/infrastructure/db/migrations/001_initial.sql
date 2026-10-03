-- Migration 001: Initial schema
-- Economist Raider — Observatorio Económico de Colombia

CREATE TABLE IF NOT EXISTS sources (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    source_type TEXT NOT NULL,
    base_url    TEXT NOT NULL,
    last_successful_run TEXT,
    last_run_at         TEXT,
    last_run_status     TEXT NOT NULL DEFAULT 'NEVER',
    last_error          TEXT,
    update_frequency    TEXT NOT NULL,
    is_active   INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS indicators (
    id                TEXT PRIMARY KEY,
    name              TEXT NOT NULL,
    category          TEXT NOT NULL,
    value             TEXT NOT NULL,
    unit              TEXT NOT NULL,
    measured_at       TEXT NOT NULL,
    period_type       TEXT NOT NULL,
    change_absolute   TEXT,
    change_pct        TEXT,
    source_id         TEXT NOT NULL REFERENCES sources(id),
    is_quarantined    INTEGER NOT NULL DEFAULT 0,
    quarantine_reason TEXT,
    created_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS measurements (
    id             TEXT PRIMARY KEY,
    indicator_name TEXT NOT NULL,
    value          TEXT NOT NULL,
    unit           TEXT NOT NULL,
    measured_at    TEXT NOT NULL,
    source_id      TEXT NOT NULL REFERENCES sources(id),
    created_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS collection_runs (
    id                  TEXT PRIMARY KEY,
    source_id           TEXT NOT NULL REFERENCES sources(id),
    started_at          TEXT NOT NULL,
    finished_at         TEXT,
    status              TEXT NOT NULL,
    records_collected   INTEGER NOT NULL DEFAULT 0,
    records_quarantined INTEGER NOT NULL DEFAULT 0,
    error_message       TEXT
);

-- Indexes for frequent queries
CREATE INDEX IF NOT EXISTS idx_indicators_name
    ON indicators(name);
CREATE INDEX IF NOT EXISTS idx_indicators_measured_at
    ON indicators(measured_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_indicators_name_date
    ON indicators(name, measured_at);
CREATE INDEX IF NOT EXISTS idx_measurements_name_date
    ON measurements(indicator_name, measured_at DESC);
CREATE INDEX IF NOT EXISTS idx_collection_runs_source
    ON collection_runs(source_id, started_at DESC);
