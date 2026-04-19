"""Configuration management for aggregator_service."""

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Application settings for local bindings and secrets.
    """
    PATIENT_SERVICE_ADDR:    str = "localhost:50051"
    CLINICAL_SERVICE_ADDR:   str = "localhost:50052"
    PHARMACY_SERVICE_ADDR:   str = "localhost:50053"
    LABORATORY_SERVICE_ADDR: str = "localhost:50054"
    MASTER_DATA_SERVICE_ADDR:str = "localhost:50055"
    JWT_SECRET_KEY: str = "super_secret_jwt_key_override_in_prod"
    JWT_ALGORITHM:  str = "HS256"

    class Config:
        env_prefix = "AGGREGATOR_SVC_"

settings = Settings()
