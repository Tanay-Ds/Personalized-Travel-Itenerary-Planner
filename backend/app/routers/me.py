from fastapi import APIRouter, Depends
from supabase import Client

from app.core.security import AuthUser, get_current_user
from app.core.supabase import get_user_supabase

router = APIRouter(tags=["me"])


@router.get("/me")
def read_me(
    user: AuthUser = Depends(get_current_user),
    db: Client = Depends(get_user_supabase),
):
    result = db.table("profiles").select("*").eq("id", user.id).limit(1).execute()
    profile = result.data[0] if result.data else None
    return {"id": user.id, "email": user.email, "profile": profile}