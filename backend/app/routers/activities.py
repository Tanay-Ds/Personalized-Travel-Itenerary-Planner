from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from supabase import Client

from app.core.security import AuthUser, get_current_user
from app.core.supabase import get_user_supabase
from app.schemas.activity import ActivityOut, ActivityUpdate
from app.services import activity_service

router = APIRouter(prefix="/activities", tags=["activities"])


@router.patch("/{activity_id}", response_model=ActivityOut)
def update_activity(
    activity_id: UUID,
    payload: ActivityUpdate,
    user: AuthUser = Depends(get_current_user),
    db: Client = Depends(get_user_supabase),
):
    return activity_service.update_activity(db, str(activity_id), payload)


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activity(
    activity_id: UUID,
    user: AuthUser = Depends(get_current_user),
    db: Client = Depends(get_user_supabase),
):
    activity_service.delete_activity(db, str(activity_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)