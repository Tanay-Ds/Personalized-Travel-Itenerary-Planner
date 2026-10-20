from supabase import Client


def insert_trip(db: Client, data: dict) -> dict:
    res = db.table("trips").insert(data).execute()
    return res.data[0]


def list_trips(db: Client) -> list[dict]:
    # RLS already limits this to trips the user owns or was invited to.
    res = db.table("trips").select("*").order("created_at", desc=True).execute()
    return res.data


def get_trip(db: Client, trip_id: str) -> dict | None:
    res = db.table("trips").select("*").eq("id", trip_id).execute()
    return res.data[0] if res.data else None


def update_trip(db: Client, trip_id: str, data: dict) -> dict | None:
    res = db.table("trips").update(data).eq("id", trip_id).execute()
    return res.data[0] if res.data else None


def delete_trip(db: Client, trip_id: str) -> bool:
    res = db.table("trips").delete().eq("id", trip_id).execute()
    return len(res.data) > 0


def get_days_with_activities(db: Client, trip_id: str) -> list[dict]:
    res = (
        db.table("itinerary_days")
        .select("*, activities(*)")
        .eq("trip_id", trip_id)
        .order("day_number")
        .execute()
    )
    return res.data


def get_days_for_trips(db: Client, trip_ids: list[str]) -> list[dict]:
    if not trip_ids:
        return []
    res = (
        db.table("itinerary_days")
        .select("trip_id, estimated_cost")
        .in_("trip_id", trip_ids)
        .execute()
    )
    return res.data