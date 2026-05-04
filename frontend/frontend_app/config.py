from pydantic_settings import BaseSettings, SettingsConfigDict


class FrontendSettings(BaseSettings):
    BACKEND_API_URL: str = "http://api:8000"
    BACKEND_PUBLIC_URL: str = "http://localhost:8000"

    model_config = SettingsConfigDict(
        env_file="./.env",
        env_ignore_empty=True,
        extra="ignore",
    )


frontend_settings = FrontendSettings()
