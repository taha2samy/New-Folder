"""Configuration management for master_data_service."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings sourced from environment variables.
    All variables must be prefixed with MASTER_DATA_SVC_ in the environment.
    """

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/reference_db"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    JWT_SECRET_KEY: str = "super_secret_jwt_key_override_in_prod"
    JWT_ALGORITHM: str = "HS256"
    GRPC_PORT: int = 50055

    class Config:
        env_prefix = "MASTER_DATA_SVC_"


settings = Settings()
