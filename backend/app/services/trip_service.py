from supabase import Client

from fastapi import HTTPException
from app.repositories import trip_repo
from app.schemas.trip import (
    TripCreate,
    TripDetailOut,
    TripOut,
    TripUpdate,
    validate_date_range,
)


# ---------- Pure helpers (tested in pytest) ----------

def compute_day_cost(activities: list[dict]) -> float:
    return round(sum(float(a.get("estimated_cost") or 0) for a in activities), 2)


def compute_trip_total(days: list[dict]) -> float:
    return round(sum(float(d.get("estimated_cost") or 0) for d in days), 2)


def build_trip_detail(trip: dict, days_raw: list[dict]) -> TripDetailOut:
    """Sort days and activities, recompute costs from the activities, nest everything."""
    days: list[dict] = []
    for d in sorted(days_raw, key=lambda x: x["day_number"]):
        acts = sorted(d.get("activities") or [], key=lambda a: a["position"])
        day = {**d, "activities": acts, "estimated_cost": compute_day_cost(acts)}
        days.append(day)
    return TripDetailOut(
        **trip,
        days=days,
        total_estimated_cost=compute_trip_total(days),
    )


def default_title(destination: str) -> str:
    return f"Trip to {destination}"


# ---------- Service functions used by the routes ----------

def create_trip(db: Client, owner_id: str, payload: TripCreate) -> TripOut:
    data = payload.model_dump(mode="json")
    data["owner_id"] = owner_id
    if not data.get("title"):
        data["title"] = default_title(payload.destination)
    # The database default is 'ready'. Plain create means no AI step, so that is correct.
    data["status"] = "ready"
    row = trip_repo.insert_trip(db, data)
    return TripOut(**row)


def list_trips(db: Client) -> list[TripOut]:
    rows = trip_repo.list_trips(db)
    ids = [r["id"] for r in rows]
    totals: dict[str, float] = {}
    for d in trip_repo.get_days_for_trips(db, ids):
        totals[d["trip_id"]] = totals.get(d["trip_id"], 0) + float(d["estimated_cost"] or 0)
    return [
        TripOut(**r, total_estimated_cost=round(totals.get(r["id"], 0), 2))
        for r in rows
    ]


def get_trip_detail(db: Client, trip_id: str) -> TripDetailOut:
    trip = trip_repo.get_trip(db, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    days_raw = trip_repo.get_days_with_activities(db, trip_id)
    return build_trip_detail(trip, days_raw)


def update_trip(db: Client, trip_id: str, payload: TripUpdate) -> TripOut:
    changes = payload.model_dump(mode="json", exclude_unset=True)

    trip = trip_repo.get_trip(db, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")

    # If only one date was sent, check it against the stored other date.
    from datetime import date

    new_start = date.fromisoformat(changes.get("start_date", trip["start_date"]))
    new_end = date.fromisoformat(changes.get("end_date", trip["end_date"]))
    try:
        validate_date_range(new_start, new_end)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    row = trip_repo.update_trip(db, trip_id, changes)
    if row is None:
        # RLS blocked it (for example an invited editor or viewer) or the trip vanished.
        raise HTTPException(status_code=403, detail="Only the trip owner can change trip details")
    return TripOut(**row)


def delete_trip(db: Client, trip_id: str) -> None:
    if not trip_repo.delete_trip(db, trip_id):
        raise HTTPException(status_code=404, detail="Trip not found or you are not the owner")
        

def reorder_day(db: Client, trip_id: str, day_number: int, activity_ids: list[str]) -> None:
    days_raw = trip_repo.get_days_with_activities(db, trip_id)
    day = next((d for d in days_raw if d["day_number"] == day_number), None)
    if day is None:
        raise HTTPException(status_code=404, detail="Day not found")
    existing = {a["id"] for a in (day.get("activities") or [])}
    if len(activity_ids) != len(existing) or set(activity_ids) != existing:
        raise HTTPException(status_code=422, detail="Activity list does not match this day")
    for pos, activity_id in enumerate(activity_ids):
        db.table("activities").update({"position": pos}).eq("id", activity_id).execute()
    