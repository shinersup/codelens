from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str = "sk-not-needed-in-mock-mode"

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

    # Mock mode — set MOCK_LLM=true in .env to skip OpenAI calls entirely
    mock_llm: bool = False

    class Config:
        env_file = ".env"


# Single instance used across the app
settings = Settings()
