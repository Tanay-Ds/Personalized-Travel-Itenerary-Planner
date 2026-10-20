from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from app.core.config import Settings, get_settings

# auto_error=False so a missing header gives 401 (not 403)
bearer_scheme = HTTPBearer(auto_error=False)

_jwks_client: PyJWKClient | None = None


def _get_jwks_client(settings: Settings) -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        # Caches the public keys so Supabase is not called on every request
        _jwks_client = PyJWKClient(settings.jwks_url, cache_keys=True, lifespan=600)
    return _jwks_client


@dataclass(frozen=True)
class AuthUser:
    id: str
    email: str | None
    token: str  # raw access token, used to build the RLS-scoped Supabase client


def _unauthorized(message: str) -> HTTPException:
    return HTTPException(
        status_code=401,
        detail=message,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> AuthUser:
    if creds is None or creds.scheme.lower() != "bearer":
        raise _unauthorized("Missing bearer token")

    token = creds.credentials
    try:
        signing_key = _get_jwks_client(settings).get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256", "RS256"],
            audience="authenticated",
            issuer=settings.jwt_issuer,
            options={"require": ["exp", "sub"]},
        )
    except jwt.ExpiredSignatureError:
        raise _unauthorized("Token has expired")
    except (jwt.PyJWTError, jwt.exceptions.PyJWKClientError):
        raise _unauthorized("Invalid token")

    return AuthUser(id=payload["sub"], email=payload.get("email"), token=token)