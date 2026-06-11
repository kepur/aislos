from pydantic import computed_field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "ainerwise-orchestrator"

    # Connects with the restricted role from scripts/setup_service_roles.sql:
    # read-only on public, read-write on ai, read-only on channels.
    ORCHESTRATOR_DB_USER: str = "ainerwise_orchestrator"
    ORCHESTRATOR_DB_PASSWORD: str = "ainerwise_orchestrator_dev"
    POSTGRES_DB: str = "ainerwise"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.ORCHESTRATOR_DB_USER}:{self.ORCHESTRATOR_DB_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    SERVICE_TOKEN: str = "ainerwise_service_dev"
    BACKEND_INTERNAL_URL: str = "http://backend:8000"

    EMBEDDING_DIM: int = 1536
    RETRIEVAL_TOP_K: int = 5
    HISTORY_MAX_MESSAGES: int = 10

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
