from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    app_name: str = "KTU Result Analyzer"
    app_version: str = "0.1.0"

    # MongoDB
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "ktu_result_analyzer"

    # JWT
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    # Google OAuth 2.0
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str = "http://localhost:3000/auth/callback"

    # WebAuthn / Passkeys
    webauthn_rp_id: str = "localhost"
    webauthn_rp_name: str = "KTU Result Analyzer"
    webauthn_origin: str = "http://localhost:3000"

    # CORS
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Cookies — set to True in production (requires HTTPS)
    cookie_secure: bool = False

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
