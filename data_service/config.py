"""Configuration for the data API service."""

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    database_url: str = Field(
        default="postgresql+psycopg2://bike_user:bike_password@localhost:5432/bike_data",
        env="DATA_DATABASE_URL",
    )
    jwt_secret: str = Field(default="change-me", env="DATA_JWT_SECRET")
    jwt_algorithm: str = "HS256"
    rate_limit: str = Field(default="50/minute", env="DATA_RATE_LIMIT")


settings = Settings()
