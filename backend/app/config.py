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

    # SMTP (email)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    smtp_from: str = ""
    smtp_use_tls: bool = True

    # Google OAuth (Gmail API)
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/email/oauth/callback"

    # Microsoft 365 / Outlook (Graph API)
    microsoft_client_id: str = ""
    microsoft_tenant_id: str = ""
    microsoft_client_secret: str = ""
    microsoft_redirect_uri: str = "https://luxis.kestinglegal.nl/api/email/oauth/callback/outlook"

    # AI Agent (Anthropic API)
    anthropic_api_key: str = ""

    # AI Agent (Moonshot/Kimi API — legacy intake model)
    kimi_api_key: str = ""

    # AI Agent (Google Gemini API — primary intake model)
    gemini_api_key: str = ""

    # Exact Online
    exact_online_client_id: str = ""
    exact_online_client_secret: str = ""
    exact_online_redirect_uri: str = "https://luxis.kestinglegal.nl/api/exact-online/callback"

    # Sentry
    sentry_dsn: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
