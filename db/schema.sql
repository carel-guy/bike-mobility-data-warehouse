-- Schema definition for bike station monitoring services

CREATE TABLE IF NOT EXISTS stations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    location JSONB NOT NULL, -- { "latitude": float, "longitude": float }
    capacity INTEGER NOT NULL CHECK (capacity >= 0),
    available_bikes INTEGER NOT NULL CHECK (available_bikes >= 0),
    broken_bikes INTEGER NOT NULL DEFAULT 0 CHECK (broken_bikes >= 0),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS events (
    id BIGSERIAL PRIMARY KEY,
    station_id TEXT NOT NULL REFERENCES stations(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    data JSONB DEFAULT '{}'::jsonb,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_station_time
    ON events (station_id, occurred_at DESC);

CREATE TABLE IF NOT EXISTS alerts (
    id BIGSERIAL PRIMARY KEY,
    station_id TEXT NOT NULL REFERENCES stations(id) ON DELETE CASCADE,
    issue_type TEXT NOT NULL,
    reported_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    data JSONB DEFAULT '{}'::jsonb,
    resolved BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_alerts_station_resolved
    ON alerts (station_id, resolved);

CREATE TABLE IF NOT EXISTS service_clients (
    client_id TEXT PRIMARY KEY,
    secret_hash TEXT NOT NULL,
    roles JSONB NOT NULL DEFAULT '["user"]'::jsonb,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO service_clients (client_id, secret_hash, roles)
VALUES (
    'dashboard-service',
    '41a5bf614853fabc117ea53b00f106bdebd914dc77bb4152df785b42779dfd4d',
    '["admin","user"]'
)
ON CONFLICT (client_id) DO NOTHING;
