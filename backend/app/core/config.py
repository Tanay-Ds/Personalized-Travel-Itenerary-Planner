from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Reads backend\.env (run uvicorn from the backend\ folder)
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_url: str
    supabase_anon_key: str
    supabase_jwt_secret: str = ""  # unused: we verify with signing keys (JWKS)

    llm_provider: str = ""
    llm_api_key: str = ""
    maps_api_key: str = ""

    allowed_origins: str = "http://localhost:5173"

    @property
    def supabase_url_clean(self) -> str:
        return self.supabase_url.rstrip("/")

    @property
    def jwks_url(self) -> str:
        return f"{self.supabase_url_clean}/auth/v1/.well-known/jwks.json"

    @property
    def jwt_issuer(self) -> str:
        return f"{self.supabase_url_clean}/auth/v1"

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()