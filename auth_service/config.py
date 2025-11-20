"""Configuration for the authentication microservice."""

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Environment-driven settings."""

    database_url: str = Field(
        default="postgresql+psycopg2://bike_user:bike_password@localhost:5432/bike_data",
        env="DATABASE_URL",
    )
    jwt_secret: str = Field(default="change-me", env="AUTH_JWT_SECRET")
    jwt_algorithm: str = "HS256"
    token_expire_minutes: int = Field(default=60, env="AUTH_TOKEN_EXPIRE_MINUTES")
    rate_limit: str = Field(default="50/minute", env="AUTH_RATE_LIMIT")


settings = Settings()
