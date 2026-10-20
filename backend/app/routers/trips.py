from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from supabase import Client

from app.core.security import AuthUser, get_current_user
from app.core.supabase import get_user_supabase
from app.schemas.trip import TripCreate, TripDetailOut, TripOut, TripUpdate
from app.services import trip_service

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