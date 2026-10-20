from datetime import time

import pytest
from pydantic import ValidationError

from app.schemas.activity import ActivityCreate, ActivityOut, ActivityUpdate
from app.schemas.day import DayOut
from app.schemas.trip import TripCreate, TripDetailOut, TripUpdate

TRIP_ID = "11111111-1111-1111-1111-111111111111"
OWNER_ID = "22222222-2222-2222-2222-222222222222"
DAY_ID = "33333333-3333-3333-3333-333333333333"
ACT_ID = "44444444-4444-4444-4444-444444444444"


def valid_trip(**overrides):
    data = {
        "destination": "Goa",
        "start_date": "2026-12-01",
        "end_date": "2026-12-05",
        "budget": 25000,
    }
    data.update(overrides)
    return data


def activity_row(**overrides):
    row = {
        "id": ACT_ID,
        "day_id": DAY_ID,
        "position": 0,
        "type": "meal",
        "title": "Breakfast",
        "description": None,
        "location_name": None,
        "lat": None,
        "lng": None,
        "start_time": "08:00:00",
        "end_time": "09:00:00",
        "estimated_cost": 250,
        "notes": None,
        "created_at": "2026-10-20T10:00:00+00:00",
    }
    row.update(overrides)
    return row


# ---------- TripCreate ----------

def test_trip_create_valid_uses_defaults():
    t = TripCreate(**valid_trip())
    assert t.currency == "INR"
    assert t.group_size == 1
    assert t.travel_style.value == "balanced"
    assert t.interests == []
    assert t.title is None


def test_trip_end_before_start_rejected():
    with pytest.raises(ValidationError):
        TripCreate(**valid_trip(start_date="2026-12-05", end_date="2026-12-01"))


def test_trip_single_day_allowed():
    TripCreate(**valid_trip(start_date="2026-12-01", end_date="2026-12-01"))


def test_trip_14_days_allowed():
    TripCreate(**valid_trip(start_date="2026-12-01", end_date="2026-12-14"))


def test_trip_15_days_rejected():
    with pytest.raises(ValidationError):
        TripCreate(**valid_trip(start_date="2026-12-01", end_date="2026-12-15"))


def test_negative_budget_rejected():
    with pytest.raises(ValidationError):
        TripCreate(**valid_trip(budget=-1))


def test_zero_budget_allowed():
    TripCreate(**valid_trip(budget=0))


@pytest.mark.parametrize("size", [0, 51])
def test_group_size_out_of_range_rejected(size):
    with pytest.raises(ValidationError):
        TripCreate(**valid_trip(group_size=size))


@pytest.mark.parametrize("size", [1, 50])
def test_group_size_edges_allowed(size):
    TripCreate(**valid_trip(group_size=size))


def test_bad_travel_style_rejected():
    with pytest.raises(ValidationError):
        TripCreate(**valid_trip(travel_style="crazy"))


def test_currency_is_uppercased():
    assert TripCreate(**valid_trip(currency="usd")).currency == "USD"


def test_bad_currency_rejected():
    with pytest.raises(ValidationError):
        TripCreate(**valid_trip(currency="RUPEES"))


def test_blank_destination_rejected():
    with pytest.raises(ValidationError):
        TripCreate(**valid_trip(destination="   "))


def test_interests_are_cleaned():
    t = TripCreate(**valid_trip(interests=[" food ", "Food", "", "temples"]))
    assert t.interests == ["food", "temples"]


# ---------- TripUpdate ----------

def test_trip_update_empty_rejected():
    with pytest.raises(ValidationError):
        TripUpdate()


def test_trip_update_partial_ok():
    u = TripUpdate(title="New name")
    assert u.model_dump(exclude_unset=True) == {"title": "New name"}


def test_trip_update_null_title_rejected():
    with pytest.raises(ValidationError):
        TripUpdate(title=None)


def test_trip_update_both_dates_bad_rejected():
    with pytest.raises(ValidationError):
        TripUpdate(start_date="2026-12-05", end_date="2026-12-01")


def test_trip_update_single_date_accepted():
    TripUpdate(end_date="2026-12-10")


# ---------- Activities ----------

def test_activity_create_valid_uses_defaults():
    a = ActivityCreate(title="Visit fort")
    assert a.type.value == "other"
    assert a.estimated_cost == 0
    assert a.position is None


def test_activity_bad_type_rejected():
    with pytest.raises(ValidationError):
        ActivityCreate(title="X", type="party")


def test_activity_negative_cost_rejected():
    with pytest.raises(ValidationError):
        ActivityCreate(title="X", estimated_cost=-5)


def test_activity_end_before_start_rejected():
    with pytest.raises(ValidationError):
        ActivityCreate(title="X", start_time="10:00", end_time="09:00")


def test_activity_lat_out_of_range_rejected():
    with pytest.raises(ValidationError):
        ActivityCreate(title="X", lat=120)


def test_activity_update_can_clear_description():
    u = ActivityUpdate(description=None)
    assert u.model_dump(exclude_unset=True) == {"description": None}


def test_activity_update_empty_rejected():
    with pytest.raises(ValidationError):
        ActivityUpdate()


# ---------- Output schemas (parsing database-style rows) ----------

def test_activity_out_from_db_row():
    a = ActivityOut(**activity_row())
    assert a.start_time == time(8, 0)
    assert a.estimated_cost == 250


def test_day_out_nests_activities():
    d = DayOut(
        id=DAY_ID,
        trip_id=TRIP_ID,
        day_number=1,
        date="2026-12-01",
        summary="Beach day",
        estimated_cost=250,
        activities=[activity_row()],
    )
    assert d.activities[0].title == "Breakfast"


def test_trip_detail_out_handles_null_interests():
    t = TripDetailOut(
        id=TRIP_ID,
        owner_id=OWNER_ID,
        title="Goa trip",
        destination="Goa",
        start_date="2026-12-01",
        end_date="2026-12-05",
        budget=25000,
        currency="INR",
        group_size=2,
        travel_style="balanced",
        interests=None,
        notes=None,
        status="ready",
        error_message=None,
        created_at="2026-10-20T10:00:00+00:00",
        updated_at="2026-10-20T10:00:00+00:00",
        days=[],
    )
    assert t.interests == []
    assert t.days == []