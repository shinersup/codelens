from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str

    # Database
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/codelens"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Auth
    secret_key: str = "dev-secret-change-in-production"
    access_token_expire_minutes: int = 60
    algorithm: str = "HS256"

    # App
    app_env: str = "development"

    class Config:
        env_file = ".env"


# Single instance used across the app
settings = Settings()
