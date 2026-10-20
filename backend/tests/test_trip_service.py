from app.services.trip_service import (
    build_trip_detail,
    compute_day_cost,
    compute_trip_total,
    default_title,
)

TRIP = {
    "id": "11111111-1111-1111-1111-111111111111",
    "owner_id": "22222222-2222-2222-2222-222222222222",
    "title": "Goa trip",
    "destination": "Goa",
    "start_date": "2026-12-01",
    "end_date": "2026-12-02",
    "budget": 10000,
    "currency": "INR",
    "group_size": 2,
    "travel_style": "balanced",
    "interests": ["food"],
    "notes": None,
    "status": "ready",
    "error_message": None,
    "created_at": "2026-10-20T10:00:00+00:00",
    "updated_at": "2026-10-20T10:00:00+00:00",
}


def act(position, cost, title="X"):
    return {
        "id": f"00000000-0000-0000-0000-00000000000{position}",
        "day_id": "33333333-3333-3333-3333-333333333333",
        "position": position,
        "type": "other",
        "title": title,
        "estimated_cost": cost,
    }


def test_day_cost_sums_activities():
    assert compute_day_cost([act(0, 100), act(1, 250.5)]) == 350.5


def test_day_cost_ignores_null_cost():
    assert compute_day_cost([{"estimated_cost": None}, act(0, 100)]) == 100


def test_day_cost_empty_is_zero():
    assert compute_day_cost([]) == 0


def test_trip_total_sums_days():
    assert compute_trip_total([{"estimated_cost": 300}, {"estimated_cost": 200}]) == 500


def test_build_detail_sorts_and_recomputes_costs():
    days_raw = [
        {
            "id": "55555555-5555-5555-5555-555555555552",
            "trip_id": TRIP["id"],
            "day_number": 2,
            "date": "2026-12-02",
            "summary": "Day two",
            "estimated_cost": 999,  # wrong on purpose, must be recomputed
            "activities": [act(0, 100)],
        },
        {
            "id": "55555555-5555-5555-5555-555555555551",
            "trip_id": TRIP["id"],
            "day_number": 1,
            "date": "2026-12-01",
            "summary": "Day one",
            "estimated_cost": 0,
            "activities": [act(1, 50, "Second"), act(0, 200, "First")],
        },
    ]
    detail = build_trip_detail(TRIP, days_raw)

    assert [d.day_number for d in detail.days] == [1, 2]
    assert [a.title for a in detail.days[0].activities] == ["First", "Second"]
    assert detail.days[0].estimated_cost == 250
    assert detail.days[1].estimated_cost == 100
    assert detail.total_estimated_cost == 350


def test_build_detail_trip_without_days():
    detail = build_trip_detail(TRIP, [])
    assert detail.days == []
    assert detail.total_estimated_cost == 0


def test_default_title():
    assert default_title("Goa") == "Trip to Goa"