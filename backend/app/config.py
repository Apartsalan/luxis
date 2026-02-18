from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://luxis:luxis_dev_password@db:5432/luxis"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # Auth
    secret_key: str = "change-this-to-a-random-string-in-production"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"

    # App
    app_env: str = "development"
    app_debug: bool = True
    cors_origins: str = "http://localhost:3000"

    # Sentry
    sentry_dsn: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
