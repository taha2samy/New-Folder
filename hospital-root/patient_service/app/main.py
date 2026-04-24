"""Entry point for patient_service."""

import asyncio
import logging
import grpc
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.generated import patient_pb2_grpc
from app.core.config import settings
from app.grpc.interceptors import AuthInterceptor
from app.grpc.handler import PatientServiceHandler
from app.events.producers import EventProducer
from app.domain.models import Base

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def serve():
    """Initializes and runs the gRPC server."""
    # Database Initialization
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    
    # Create tables for demonstration purposes. 
    # In production, use Alembic migrations instead.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async_session_factory = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )

    # Kafka Producer Initialization
    producer = EventProducer()
    try:
        await producer.start()
        logger.info("Kafka Producer started successfully.")
    except Exception as e:
        logger.error(f"Failed to start Kafka Producer (fire-and-forget fallback): {e}")
    
    # gRPC Server Initialization
    server = grpc.aio.server(
        interceptors=(AuthInterceptor(),)
    )
    
    handler = PatientServiceHandler(
        db_session_factory=async_session_factory,
        event_producer=producer
    )
    
    patient_pb2_grpc.add_PatientServiceServicer_to_server(handler, server)
    
    listen_addr = f"[::]:{settings.GRPC_PORT}"
    server.add_insecure_port(listen_addr)
    
    logger.info(f"Starting Patient gRPC Service on {listen_addr}...")
    await server.start()
    
    try:
        await server.wait_for_termination()
    except asyncio.CancelledError:
        logger.info("Termination signal received. Shutting down gracefully...")
    finally:
        await server.stop(grace=5)
        await producer.stop()
        await engine.dispose()
        logger.info("Shutdown complete.")

if __name__ == "__main__":
    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        logger.info("Service interrupted by user.")
