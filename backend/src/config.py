from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/langsmith"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
