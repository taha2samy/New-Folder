"""Configuration management for clinical_service."""

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Application settings, loaded from environment variables or .env file.
    """
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/clinical_db"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    PATIENT_SERVICE_ADDR: str = "localhost:50051"
    MASTER_DATA_SERVICE_ADDR: str = "localhost:50055"
    BILLING_SERVICE_ADDR: str = "localhost:50056"
    JWT_SECRET_KEY: str = "super_secret_jwt_key_override_in_prod"
    JWT_ALGORITHM: str = "HS256"
    GRPC_PORT: int = 50052

    class Config:
        env_prefix = "CLINICAL_SVC_"

settings = Settings()


