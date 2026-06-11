from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "ProcurePing Backend"
    APP_ENV: str = "development"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/procureping"
    JWT_SECRET: str = "change-me-to-a-random-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    UPLOAD_STORAGE: str = "local"
    UPLOAD_DIR: str = "./uploads"
    PUBLIC_FILE_BASE_URL: str = "http://localhost:8000/uploads"
    UPLOAD_MAX_SIZE_MB: int = 10
    UPLOAD_ALLOWED_TYPES: str = "image/jpeg,image/png,image/webp,application/pdf"

    EMAIL_ENABLED: bool = False
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "no-reply@procureping.local"

    TELEGRAM_ENABLED: bool = False
    TELEGRAM_BOT_TOKEN: str = ""

    ESCROW_PROVIDER: str = "SIMULATED"
    ESCROW_AUTO_CAPTURE: bool = True

    MAPS_PROVIDER: str = "LOCAL"
    GOOGLE_MAPS_API_KEY: str = ""
    DEFAULT_MAP_COUNTRY: str = "Philippines"
    DEFAULT_MAP_CITY: str = "Cebu City"

    # AI provider config — these env vars serve as fallback when platform_settings is empty
    OPENAI_API_KEY: str = ""
    AI_PROVIDER: str = ""  # openai | anthropic
    AI_MODEL: str = ""     # e.g. gpt-4o-mini

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def upload_allowed_types_list(self) -> list[str]:
        return [t.strip() for t in self.UPLOAD_ALLOWED_TYPES.split(",") if t.strip()]


settings = Settings()
