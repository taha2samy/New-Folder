"""Main entry point for Pharmacy Service."""

import asyncio
import logging
import grpc
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from generated import pharmacy_pb2_grpc
from app.grpc.handler import PharmacyServiceHandler
from app.grpc.interceptors import AuthInterceptor
from app.events.producers import PharmacyEventProducer
from app.domain.models import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def serve():
    # Database Setup
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    # Make sure tables are created (in a real app, use Alembic migrations)
    async with engine.begin() as conn:
         await conn.run_sync(Base.metadata.create_all)

    # Services
    event_producer = PharmacyEventProducer()

    # gRPC Setup
    server = grpc.aio.server(
        interceptors=(AuthInterceptor(),)
    )
    
    pharmacy_pb2_grpc.add_PharmacyServiceServicer_to_server(
        PharmacyServiceHandler(async_session, event_producer), server
    )

    listen_addr = f"[::]:{settings.GRPC_PORT}"
    server.add_insecure_port(listen_addr)
    
    logger.info(f"Starting Pharmacy gRPC server on {listen_addr}")
    await server.start()
    
    try:
        await server.wait_for_termination()
    except asyncio.CancelledError:
        logger.info("Gracefully shutting down...")
        event_producer.flush()

if __name__ == "__main__":
    asyncio.run(serve())
