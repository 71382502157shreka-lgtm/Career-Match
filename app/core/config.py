"""
Centralized application configuration.
Values are read from environment variables / a .env file, with sane
defaults for local development.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Job Finder"
    API_V1_STR: str = "/api/v1"

    SECRET_KEY: str = "CHANGE_THIS_SECRET_KEY_IN_PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    DATABASE_URL: str = "sqlite:///./job_finder.db"

    # AI matching engine tuning
    MIN_MATCH_SCORE: float = 10.0  # ignore matches below this % score

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
