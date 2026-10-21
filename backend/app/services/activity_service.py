from fastapi import HTTPException
from supabase import Client

from app.repositories import trip_repo
from app.schemas.activity import ActivityOut, ActivityUpdate
from app.services.trip_service import compute_day_cost


def _recalculate_day_cost(db: Client, day_id: str) -> None:
    acts = trip_repo.get_activities_for_day(db, day_id)
    trip_repo.update_day_cost(db, day_id, compute_day_cost(acts))


def update_activity(db: Client, activity_id: str, payload: ActivityUpdate) -> ActivityOut:
    changes = payload.model_dump(mode="json", exclude_unset=True)

    existing = trip_repo.get_activity(db, activity_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Activity not found")

    row = trip_repo.update_activity(db, activity_id, changes)
    if row is None:
        raise HTTPException(status_code=403, detail="You are not allowed to edit this activity")

    _recalculate_day_cost(db, row["day_id"])
    return ActivityOut(**row)


def delete_activity(db: Client, activity_id: str) -> None:
    existing = trip_repo.get_activity(db, activity_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Activity not found")

    if not trip_repo.delete_activity(db, activity_id):
        raise HTTPException(status_code=403, detail="You are not allowed to delete this activity")

    _recalculate_day_cost(db, existing["day_id"])