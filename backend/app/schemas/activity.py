from datetime import datetime, time
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ActivityType(str, Enum):
    attraction = "attraction"
    meal = "meal"
    stay = "stay"
    transport = "transport"
    other = "other"


def check_time_order(start: time | None, end: time | None) -> None:
    if start is not None and end is not None and end <= start:
        raise ValueError("end_time must be after start_time")


class ActivityBase(BaseModel):
    """Fields shared by create and output. No cross-field checks here,
    so data coming back from the database never fails validation."""

    model_config = ConfigDict(str_strip_whitespace=True)

    type: ActivityType = ActivityType.other
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    location_name: str | None = Field(default=None, max_length=200)
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    start_time: time | None = None
    end_time: time | None = None
    estimated_cost: float = Field(default=0, ge=0)
    notes: str | None = Field(default=None, max_length=2000)


class ActivityCreate(ActivityBase):
    # If position is left out, the service will add the activity at the end of the day.
    position: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def times_in_order(self):
        check_time_order(self.start_time, self.end_time)
        return self


class ActivityUpdate(BaseModel):
    """Every field is optional. Only fields the client actually sends are changed.
    For fields that cannot be empty in the database (type, title, estimated_cost),
    an explicit null is rejected. Fields that can be cleared accept null."""

    model_config = ConfigDict(str_strip_whitespace=True)

    type: ActivityType = None
    title: str = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    location_name: str | None = Field(default=None, max_length=200)
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    start_time: time | None = None
    end_time: time | None = None
    estimated_cost: float = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def check_update(self):
        if not self.model_fields_set:
            raise ValueError("Send at least one field to update")
        check_time_order(self.start_time, self.end_time)
        return self


class ActivityOut(ActivityBase):
    id: UUID
    day_id: UUID
    position: int
    created_at: datetime | None = None