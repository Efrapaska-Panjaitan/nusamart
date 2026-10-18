import json
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "NusaMart API"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    secret_key: str = "unsafe-development-secret-change-me"
    access_token_expire_minutes: int = 30
    database_url: str = "postgresql+psycopg://nusamart:nusamart_dev_password@localhost:5432/nusamart"
    cors_origins: str = '["http://localhost:5173"]'
    admin_email: str = "admin@nusamart.local"
    admin_password: str = "Admin1234!"
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        value = self.cors_origins.strip()
        if value.startswith("["):
            parsed = json.loads(value)
            if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
                raise ValueError("CORS_ORIGINS must be a JSON array of strings")
            return parsed
        return [item.strip() for item in value.split(",") if item.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()
