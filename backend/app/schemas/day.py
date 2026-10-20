from datetime import date as date_type
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.activity import ActivityOut


class DayOut(BaseModel):
    id: UUID
    trip_id: UUID
    day_number: int = Field(ge=1)
    date: date_type | None = None
    summary: str | None = None
    estimated_cost: float = 0
    activities: list[ActivityOut] = Field(default_factory=list)