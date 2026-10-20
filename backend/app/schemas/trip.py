from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.day import DayOut

MAX_TRIP_DAYS = 14


class TravelStyle(str, Enum):
    relaxed = "relaxed"
    balanced = "balanced"
    packed = "packed"


class TripStatus(str, Enum):
    generating = "generating"
    ready = "ready"
    failed = "failed"


def validate_date_range(start: date, end: date) -> None:
    """Shared rule. The service reuses this when only one date is updated."""
    if end < start:
        raise ValueError("end_date must be on or after start_date")
    if (end - start).days > MAX_TRIP_DAYS - 1:
        raise ValueError(f"A trip can be at most {MAX_TRIP_DAYS} days long")


def normalise_currency(value: str) -> str:
    value = value.strip().upper()
    if len(value) != 3 or not value.isalpha():
        raise ValueError("currency must be a 3-letter code such as INR")
    return value


def clean_interests(values: list[str]) -> list[str]:
    cleaned: list[str] = []
    for item in values:
        item = item.strip()
        if not item:
            continue
        if len(item) > 50:
            raise ValueError("each interest must be 50 characters or fewer")
        if item.lower() not in [c.lower() for c in cleaned]:
            cleaned.append(item)
    return cleaned


class TripCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=1, max_length=120)
    destination: str = Field(min_length=1, max_length=120)
    start_date: date
    end_date: date
    budget: float = Field(ge=0)
    currency: str = "INR"
    group_size: int = Field(default=1, ge=1, le=50)
    travel_style: TravelStyle = TravelStyle.balanced
    interests: list[str] = Field(default_factory=list, max_length=20)
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("currency")
    @classmethod
    def currency_ok(cls, v: str) -> str:
        return normalise_currency(v)

    @field_validator("interests")
    @classmethod
    def interests_ok(cls, v: list[str]) -> list[str]:
        return clean_interests(v)

    @model_validator(mode="after")
    def dates_ok(self):
        validate_date_range(self.start_date, self.end_date)
        return self


class TripUpdate(BaseModel):
    """All fields optional. Status cannot be changed by the user.
    If only ONE date is sent, the service checks it against the stored trip."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(default=None, min_length=1, max_length=120)
    destination: str = Field(default=None, min_length=1, max_length=120)
    start_date: date = None
    end_date: date = None
    budget: float = Field(default=None, ge=0)
    currency: str = None
    group_size: int = Field(default=None, ge=1, le=50)
    travel_style: TravelStyle = None
    interests: list[str] = Field(default=None, max_length=20)
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("currency")
    @classmethod
    def currency_ok(cls, v: str) -> str:
        return normalise_currency(v)

    @field_validator("interests")
    @classmethod
    def interests_ok(cls, v: list[str]) -> list[str]:
        return clean_interests(v)

    @model_validator(mode="after")
    def check_update(self):
        if not self.model_fields_set:
            raise ValueError("Send at least one field to update")
        if self.start_date is not None and self.end_date is not None:
            validate_date_range(self.start_date, self.end_date)
        return self


class TripOut(BaseModel):
    id: UUID
    owner_id: UUID
    title: str | None = None
    destination: str
    start_date: date
    end_date: date
    budget: float | None = None
    currency: str = "INR"
    group_size: int = 1
    travel_style: TravelStyle = TravelStyle.balanced
    interests: list[str] = Field(default_factory=list)
    notes: str | None = None
    status: TripStatus
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    # Not stored in the database. The service computes it from the day costs.
    total_estimated_cost: float = 0

    @field_validator("interests", mode="before")
    @classmethod
    def interests_null_to_empty(cls, v):
        return [] if v is None else v


class TripDetailOut(TripOut):
    days: list[DayOut] = Field(default_factory=list)