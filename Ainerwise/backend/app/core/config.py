from pydantic_settings import BaseSettings
from pydantic import computed_field


class Settings(BaseSettings):
    PROJECT_NAME: str = "AinerWise"
    API_V1_PREFIX: str = "/api/v1"

    POSTGRES_USER: str = "ainerwise"
    POSTGRES_PASSWORD: str = "ainerwise_dev_2024"
    POSTGRES_DB: str = "ainerwise"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @computed_field
    @property
    def DATABASE_URL_SYNC(self) -> str:
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = "ainerwise_redis_dev"

    @computed_field
    @property
    def REDIS_URL(self) -> str:
        return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ROOT_USER: str = "ainerwise"
    MINIO_ROOT_PASSWORD: str = "ainerwise_minio_dev"
    MINIO_USE_SSL: bool = False

    SECRET_KEY: str = "change-this-to-a-random-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:4097",
        "http://localhost:4098",
        "http://localhost:4099",
        "http://127.0.0.1:4097",
        "http://127.0.0.1:4098",
        "http://127.0.0.1:4099",
        "http://localhost:8000",
        "http://localhost",
    ]
    BACKEND_CORS_ORIGIN_REGEX: str = (
        r"^https?://("
        r"localhost|127\.0\.0\.1|"
        r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
        r"172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}|"
        r"192\.168\.\d{1,3}\.\d{1,3}"
        r")(:\d+)?$"
    )

    DEMO_MODE_ENABLED: bool = True
    DEMO_BUYER_EMAIL: str = "demo@ainerwise.com"
    DEMO_BUYER_PASSWORD: str = "demo123"
    DEMO_ADMIN_EMAIL: str = "admin@ainerwise.com"
    DEMO_ADMIN_PASSWORD: str = "admin123456"

    # Procurement Portal Context: the gateway strips external X-Portal-Key
    # headers and injects the trusted value; the default key is a local-dev
    # fallback only and must stay empty in production.
    PROCUREMENT_PORTAL_HEADER: str = "X-Portal-Key"
    PROCUREMENT_DEFAULT_PORTAL_KEY: str = ""

    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_ADMIN_CHAT_ID: str = ""
    AI_ORCHESTRATOR_URL: str = "http://ai-orchestrator:8001"
    CHANNEL_GATEWAY_URL: str = "http://channel-gateway:8200"
    PARTNER_PORTAL_URL: str = "http://localhost:4098"
    SIGN_BASE_URL: str = "http://localhost:4099"
    SERVICE_TOKEN: str = "ainerwise_service_dev"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
