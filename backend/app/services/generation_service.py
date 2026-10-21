from datetime import timedelta

from fastapi import HTTPException
from supabase import Client

from app.repositories import trip_repo
from app.schemas.trip import TripCreate
from app.services import ai_service


def generate_trip(db: Client, user_id: str, payload: TripCreate) -> str:
    num_days = (payload.end_date - payload.start_date).days + 1

    trip_data = {
        "title": payload.title or f"Trip to {payload.destination}",
        "destination": payload.destination,
        "start_date": payload.start_date.isoformat(),
        "end_date": payload.end_date.isoformat(),
        "budget": payload.budget,
        "currency": payload.currency,
        "group_size": payload.group_size,
        "travel_style": payload.travel_style.value,
        "interests": payload.interests,
        "notes": payload.notes,
    }

    # 1. Ask the AI first. If it fails, nothing is saved.
    itinerary = ai_service.generate_itinerary(trip_data, num_days)

    # 2. Save the trip. Status is set explicitly (DB default is 'ready').
    trip = trip_repo.insert_trip(
        db, {**trip_data, "owner_id": str(user_id), "status": "ready"}
    )
    trip_id = trip["id"]

    try:
        # 3. Save days with costs recomputed in Python.
        day_rows = []
        for i, day in enumerate(itinerary.days):
            day_rows.append(
                {
                    "trip_id": trip_id,
                    "day_number": i + 1,
                    "date": (payload.start_date + timedelta(days=i)).isoformat(),
                    "summary": day.summary,
                    "estimated_cost": round(sum(a.estimated_cost for a in day.activities), 2),
                }
            )
        saved_days = db.table("itinerary_days").insert(day_rows).execute().data
        id_by_number = {d["day_number"]: d["id"] for d in saved_days}

        # 4. Save activities for all days in one insert.
        activity_rows = []
        for i, day in enumerate(itinerary.days):
            day_id = id_by_number[i + 1]
            for pos, a in enumerate(day.activities):
                end = a.end_time
                if a.start_time and end and end <= a.start_time:
                    end = None
                activity_rows.append(
                    {
                        "day_id": day_id,
                        "position": pos,
                        "type": a.type,
                        "title": a.title,
                        "description": a.description,
                        "location_name": a.location_name,
                        "start_time": a.start_time.isoformat() if a.start_time else None,
                        "end_time": end.isoformat() if end else None,
                        "estimated_cost": round(a.estimated_cost, 2),
                    }
                )
        db.table("activities").insert(activity_rows).execute()
    except Exception as e:
        # Do not leave a half-saved trip behind.
        try:
            trip_repo.delete_trip(db, trip_id)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Could not save itinerary: {e}")

    return trip_id
    

def regenerate_day(db: Client, trip_id: str, day_number: int) -> None:
    trip = trip_repo.get_trip(db, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")

    days_raw = trip_repo.get_days_with_activities(db, trip_id)
    day = next((d for d in days_raw if d["day_number"] == day_number), None)
    if day is None:
        raise HTTPException(status_code=404, detail="Day not found")

    old_ids = [a["id"] for a in (day.get("activities") or [])]
    avoid_titles = [
        a["title"]
        for d in days_raw
        if d["day_number"] != day_number
        for a in (d.get("activities") or [])
    ]

    # 1. Ask the AI first. If it fails, the old day stays untouched.
    new_day = ai_service.generate_single_day(
        trip, day_number, len(days_raw), avoid_titles
    )

    # 2. Insert the new activities BEFORE deleting the old ones (safer).
    rows = []
    for pos, a in enumerate(new_day.activities):
        end = a.end_time
        if a.start_time and end and end <= a.start_time:
            end = None
        rows.append(
            {
                "day_id": day["id"],
                "position": pos,
                "type": a.type,
                "title": a.title,
                "description": a.description,
                "location_name": a.location_name,
                "start_time": a.start_time.isoformat() if a.start_time else None,
                "end_time": end.isoformat() if end else None,
                "estimated_cost": round(a.estimated_cost, 2),
            }
        )
    try:
        db.table("activities").insert(rows).execute()
        if old_ids:
            db.table("activities").delete().in_("id", old_ids).execute()
        db.table("itinerary_days").update(
            {
                "summary": new_day.summary,
                "estimated_cost": round(sum(a.estimated_cost for a in new_day.activities), 2),
            }
        ).eq("id", day["id"]).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save regenerated day: {e}")