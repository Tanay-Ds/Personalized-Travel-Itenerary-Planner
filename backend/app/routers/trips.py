from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from supabase import Client

from app.core.security import AuthUser, get_current_user
from app.core.supabase import get_user_supabase
from app.schemas.trip import TripCreate, TripDetailOut, TripOut, TripUpdate
from app.services import generation_service, trip_service

router = APIRouter(prefix="/trips", tags=["trips"])


@router.post("", response_model=TripOut, status_code=status.HTTP_201_CREATED)
def create_trip(
    payload: TripCreate,
    user: AuthUser = Depends(get_current_user),
    db: Client = Depends(get_user_supabase),
):
    return trip_service.create_trip(db, user.id, payload)


@router.get("", response_model=list[TripOut])
def list_trips(
    user: AuthUser = Depends(get_current_user),
    db: Client = Depends(get_user_supabase),
):
    return trip_service.list_trips(db)


@router.get("/{trip_id}", response_model=TripDetailOut)
def get_trip(
    trip_id: UUID,
    user: AuthUser = Depends(get_current_user),
    db: Client = Depends(get_user_supabase),
):
    return trip_service.get_trip_detail(db, str(trip_id))


@router.patch("/{trip_id}", response_model=TripOut)
def update_trip(
    trip_id: UUID,
    payload: TripUpdate,
    user: AuthUser = Depends(get_current_user),
    db: Client = Depends(get_user_supabase),
):
    return trip_service.update_trip(db, str(trip_id), payload)


@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trip(
    trip_id: UUID,
    user: AuthUser = Depends(get_current_user),
    db: Client = Depends(get_user_supabase),
):
    trip_service.delete_trip(db, str(trip_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
@router.post("/generate", response_model=TripDetailOut, status_code=status.HTTP_201_CREATED)
def generate_trip(
    payload: TripCreate,
    user: AuthUser = Depends(get_current_user),
    db: Client = Depends(get_user_supabase),
):
    # Synchronous on purpose (prototype mode): takes roughly 10-20 seconds.
    trip_id = generation_service.generate_trip(db, user.id, payload)
    return trip_service.get_trip_detail(db, trip_id)
    

@router.post("/{trip_id}/days/{day_number}/regenerate", response_model=TripDetailOut)
def regenerate_day(
    trip_id: UUID,
    day_number: int,
    user: AuthUser = Depends(get_current_user),
    db: Client = Depends(get_user_supabase),
):
    generation_service.regenerate_day(db, str(trip_id), day_number)
    return trip_service.get_trip_detail(db, str(trip_id))
    

from pydantic import BaseModel


class ReorderIn(BaseModel):
    activity_ids: list[str]


@router.post("/{trip_id}/days/{day_number}/reorder", response_model=TripDetailOut)
def reorder_day(
    trip_id: UUID,
    day_number: int,
    payload: ReorderIn,
    user: AuthUser = Depends(get_current_user),
    db: Client = Depends(get_user_supabase),
):
    trip_service.reorder_day(db, str(trip_id), day_number, payload.activity_ids)
    return trip_service.get_trip_detail(db, str(trip_id))