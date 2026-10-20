from fastapi import Depends
from supabase import Client, create_client

from app.core.config import Settings, get_settings
from app.core.security import AuthUser, get_current_user


def get_user_supabase(
    user: AuthUser = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> Client:
    """Supabase client acting AS the user, so RLS applies to every query.
    Created per request and never shared between users."""
    client = create_client(settings.supabase_url_clean, settings.supabase_anon_key)
    client.postgrest.auth(user.token)
    return client