"""Entry point for clinical_service."""

import asyncio
import logging
import grpc
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from generated import clinical_pb2_grpc
from app.core.config import settings
from app.grpc.interceptors import AuthInterceptor
from app.grpc.handler import ClinicalEncounterServiceHandler
from app.events.producers import EncounterEventProducer
from app.events.consumers import PatientEventConsumer
from app.grpc_clients.patient_client import PatientServiceClient
from app.domain.models import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def serve():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async_session_factory = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    producer = EncounterEventProducer()
    consumer = PatientEventConsumer(async_session_factory)
    client = PatientServiceClient()

    try:
        await producer.start()
        await consumer.start()
        logger.info("Kafka components initialized.")
    except Exception as e:
        logger.error(f"Kafka error (fire and forget overrides): {e}")

    server = grpc.aio.server(interceptors=(AuthInterceptor(),))
    
    handler = ClinicalEncounterServiceHandler(
        db_session_factory=async_session_factory,
        event_producer=producer,
        patient_client=client
    )
    
    clinical_pb2_grpc.add_ClinicalEncounterServiceServicer_to_server(handler, server)
    
    listen_addr = f"[::]:{settings.GRPC_PORT}"
    server.add_insecure_port(listen_addr)
    
    logger.info(f"Starting Clinical Encounter gRPC Service on {listen_addr}...")
    await server.start()
    
    try:
        await server.wait_for_termination()
    except asyncio.CancelledError:
        logger.info("Termination signal received. Shutting down gracefully...")
    finally:
        await server.stop(grace=5)
        await consumer.stop()
        await producer.stop()
        await engine.dispose()
        logger.info("Shutdown complete.")

if __name__ == "__main__":
    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        logger.info("Service interrupted by user.")
