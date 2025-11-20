"""FastAPI data service exposing station analytics endpoints."""

from typing import List

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Path, status
from slowapi import Limiter
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy import text
from sqlalchemy.orm import Session

from .auth import require_admin, require_user
from .config import settings
from .db import get_db
from .models import Alert, Station, StationDetail, StationEvent, TopStation

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit])

app = FastAPI(title="Bike Data Service", version="0.2.0")
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

protected_router = APIRouter(dependencies=[Depends(require_user)], tags=["Protected"])


@app.get("/", tags=["Public"], description="Public endpoint, no authentication required")
def public_root():
    """Simple greeting exposed without authentication."""
    return {"message": "Hello, this is the only public route for now!"}


@protected_router.get("/secret", description="Protected endpoint that requires an access token")
def protected_secret():
    """Show a secret message to authenticated clients."""
    return {"message": 'The password is "platypus". Shhhht, it\'s a secret!'}


@app.get("/stations", response_model=List[Station], tags=["Protected"])
def list_stations(
    db: Session = Depends(get_db),
    user=Depends(require_user),
):
    """Return the latest status for every station."""
    query = text(
        """
        SELECT id,
               name,
               capacity,
               available_bikes,
               broken_bikes,
               updated_at,
               location
        FROM stations
        ORDER BY name
        """
    )
    rows = db.execute(query).mappings().all()
    return [Station(**row) for row in rows]


@app.get("/stations/top10", response_model=List[TopStation], tags=["Protected"])
def most_active_stations(
    db: Session = Depends(get_db),
    user=Depends(require_user),
):
    """Return the ten stations with the highest average hourly movement."""
    query = text(
        """
        WITH hourly AS (
            SELECT station_id,
                   date_trunc('hour', occurred_at) AS hour_bucket,
                   COUNT(*) AS events
            FROM events
            GROUP BY station_id, hour_bucket
        )
        SELECT s.id,
               s.name,
               COALESCE(AVG(hourly.events), 0) AS avg_events_per_hour
        FROM stations s
        LEFT JOIN hourly ON hourly.station_id = s.id
        GROUP BY s.id, s.name
        ORDER BY avg_events_per_hour DESC
        LIMIT 10
        """
    )
    rows = db.execute(query).mappings().all()
    return [TopStation(**row) for row in rows]


@app.get("/stations/{station_id}", response_model=StationDetail, tags=["Protected"])
def station_detail(
    station_id: str = Path(..., description="Station identifier"),
    db: Session = Depends(get_db),
    user=Depends(require_user),
):
    """Return station status plus recent event history."""
    station_query = text(
        """
        SELECT id,
               name,
               capacity,
               available_bikes,
               broken_bikes,
               updated_at,
               location
        FROM stations
        WHERE id = :station_id
        """
    )
    station_row = db.execute(station_query, {"station_id": station_id}).mappings().one_or_none()
    if not station_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Station not found.")

    events_query = text(
        """
        SELECT id,
               station_id,
               event_type,
               data,
               occurred_at
        FROM events
        WHERE station_id = :station_id
        ORDER BY occurred_at DESC
        LIMIT 50
        """
    )
    event_rows = db.execute(events_query, {"station_id": station_id}).mappings().all()
    events = [StationEvent(**row) for row in event_rows]
    return StationDetail(**station_row, events=events)


@app.get("/alerts", response_model=List[Alert], tags=["Protected"])
def list_alerts(
    db: Session = Depends(get_db),
    user=Depends(require_admin),
):
    """Return active alerts (admin only)."""
    query = text(
        """
        SELECT id,
               station_id,
               issue_type,
               reported_at,
               data,
               resolved
        FROM alerts
        WHERE resolved = FALSE
        ORDER BY reported_at DESC
        """
    )
    rows = db.execute(query).mappings().all()
    return [Alert(**row) for row in rows]


app.include_router(protected_router)
