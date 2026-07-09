from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://luxis:luxis_dev_password@db:5432/luxis"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # Auth
    secret_key: str = "change-this-to-a-random-string-in-production"
    token_encryption_key: str = ""
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
    # Bouwfase-noodslot: True = álle uitgaande mail geblokkeerd (alle providers + SMTP).
    outbound_mail_lock: bool = False

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

    # AI Agent — unused since S159 — AVG B1 (Kimi/Moonshot uit code: PII naar China)
    # Settings behouden voor backwards-compat .env; nergens meer gelezen.
    kimi_api_key: str = ""

    # AI Agent — unused since S159 — AVG B1 (Gemini uit code: gratis-tier traint op data)
    gemini_api_key: str = ""

    # Exact Online
    exact_online_client_id: str = ""
    exact_online_client_secret: str = ""
    exact_online_redirect_uri: str = "https://luxis.kestinglegal.nl/api/exact-online/callback"

    # Sentry
    sentry_dsn: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()


# ── SECRET_KEY hardening (AUDIT-B1) ──────────────────────────────────────────
# Known weak/placeholder keys that must never sign tokens in production. A
# forged token signed with one of these would otherwise be accepted as valid.
SECRET_KEY_BLACKLIST = frozenset(
    {
        "change-this-to-a-random-string-in-production",
        "dev-secret-key-change-in-production",
        "secret",
        "password",
    }
)

# Default-secure: ONLY these environments may boot with a weak SECRET_KEY.
# Anything else — including an unset, empty, or misspelled APP_ENV — is treated
# as production and must have a strong key. This closes the misconfiguration
# hole where a typo'd APP_ENV silently disables the production guard.
SECRET_KEY_DEV_ENVS = frozenset(
    {"development", "dev", "test", "testing", "local", "ci"}
)

MIN_SECRET_KEY_LENGTH = 32


def secret_key_status(secret_key: str, app_env: str) -> tuple[bool, bool]:
    """Classify the SECRET_KEY for startup validation.

    Returns ``(is_weak, is_enforced)``:
    - ``is_weak``: the key is a known placeholder or shorter than 32 chars.
    - ``is_enforced``: this environment must refuse to start on a weak key
      (i.e. it is NOT an explicit development/test environment).
    """
    is_weak = secret_key in SECRET_KEY_BLACKLIST or len(secret_key) < MIN_SECRET_KEY_LENGTH
    is_enforced = app_env.lower().strip() not in SECRET_KEY_DEV_ENVS
    return is_weak, is_enforced
