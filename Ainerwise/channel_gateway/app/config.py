from pydantic import computed_field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    POSTGRES_USER: str = "ainerwise"
    POSTGRES_PASSWORD: str = "ainerwise_dev_2024"
    POSTGRES_DB: str = "ainerwise"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    BACKEND_INTERNAL_URL: str = "http://backend:8000/internal/v1"
    SERVICE_TOKEN: str = "ainerwise_service_dev"
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_WEBHOOK_SECRET: str = ""

    @computed_field
    @property
    def DATABASE_DSN(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
