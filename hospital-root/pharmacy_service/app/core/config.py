"""Configuration management for pharmacy_service."""

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Application settings, loaded from environment variables or .env file.
    """
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/pharmacy_db"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    JWT_SECRET_KEY: str = "super_secret_jwt_key_override_in_prod"
    JWT_ALGORITHM: str = "HS256"
    GRPC_PORT: int = 50053

    class Config:
        env_prefix = "PHARMACY_SVC_"

settings = Settings()
