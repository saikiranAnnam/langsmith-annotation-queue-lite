from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/langsmith"
    requeue_stuck_entries_enabled: bool = True
    requeue_stuck_entries_interval: int = 300  # 5 minutes
    requeue_stuck_entries_threshold: int = 30  # 30 minutes

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
