from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GRPC_PORT: int = 50056
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/billing_db"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    JWT_SECRET_KEY: str = "supersecretkey"
    JWT_ALGORITHM: str = "HS256"
    
    MASTER_DATA_SERVICE_ADDR: str = "localhost:50055"
    CLINICAL_SERVICE_ADDR: str = "localhost:50051"
    INTERNAL_API_SECRET: str = "hms-system-internal-secret-2026"

    class Config:
        env_file = ".env"

settings = Settings()
