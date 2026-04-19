"""Main entry point for Laboratory Service.

Bootstraps the async SQLAlchemy engine, wires the Kafka event producer, and
starts the gRPC server with the JWT authentication interceptor attached.
"""

import asyncio
import logging

import grpc
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.domain.models import Base
from app.events.producers import LaboratoryEventProducer
from app.grpc.handler import LaboratoryServiceHandler
from app.grpc.interceptors import AuthInterceptor
from app.grpc_clients.master_data_client import MasterDataClient
from generated import laboratory_pb2_grpc

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


async def serve() -> None:
    """Configure and start the asynchronous gRPC server."""

    # ------------------------------------------------------------------ #
    # Database                                                             #
    # ------------------------------------------------------------------ #
    engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Ensure schema exists; production deployments rely on Alembic migrations.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # ------------------------------------------------------------------ #
    # Kafka producer                                                       #
    # ------------------------------------------------------------------ #
    event_producer = LaboratoryEventProducer()

    # ------------------------------------------------------------------ #
    # gRPC server                                                          #
    # ------------------------------------------------------------------ #
    server = grpc.aio.server(interceptors=(AuthInterceptor(),))
    
    master_data_client = MasterDataClient()

    laboratory_pb2_grpc.add_LaboratoryServiceServicer_to_server(
        LaboratoryServiceHandler(async_session, event_producer, master_data_client),
        server,
    )

    listen_addr = f"[::]:{settings.GRPC_PORT}"
    server.add_insecure_port(listen_addr)

    logger.info("Laboratory gRPC server starting on %s", listen_addr)
    await server.start()

    try:
        await server.wait_for_termination()
    except asyncio.CancelledError:
        logger.info("Shutdown signal received — flushing Kafka producer...")
        event_producer.flush()
        logger.info("Laboratory service shut down cleanly.")


if __name__ == "__main__":
    asyncio.run(serve())
