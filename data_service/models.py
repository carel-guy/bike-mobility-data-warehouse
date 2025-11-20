"""Pydantic response models for the data service."""

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class Station(BaseModel):
    id: str
    name: str
    capacity: int
    available_bikes: int = Field(..., alias="available_bikes")
    broken_bikes: int
    updated_at: datetime
    location: dict[str, float]

    class Config:
        populate_by_name = True


class StationEvent(BaseModel):
    id: int
    station_id: str
    event_type: str
    data: dict[str, Any]
    occurred_at: datetime


class StationDetail(Station):
    events: List[StationEvent] = []


class TopStation(BaseModel):
    id: str
    name: str
    avg_events_per_hour: float


class Alert(BaseModel):
    id: int
    station_id: str
    issue_type: str
    reported_at: datetime
    data: Optional[dict[str, Any]] = None
    resolved: bool
