"""Main entry point for Master Data Service.

Bootstraps the async SQLAlchemy engine, wires the Kafka event producer, and
starts the gRPC server with the JWT authentication interceptor attached.
The service is intentionally stateless so it can be horizontally scaled to
satisfy the system's high-read requirements.
"""

import asyncio
import logging

import grpc
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.domain.models import Base
from app.events.producers import MasterDataEventProducer
from app.grpc.handler import MasterDataServiceHandler
from app.grpc.interceptors import AuthInterceptor
from app.generated import master_data_pb2_grpc

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
    event_producer = MasterDataEventProducer()

    # ------------------------------------------------------------------ #
    # gRPC server                                                          #
    # ------------------------------------------------------------------ #
    server = grpc.aio.server(interceptors=(AuthInterceptor(),))

    master_data_pb2_grpc.add_MasterDataServiceServicer_to_server(
        MasterDataServiceHandler(async_session, event_producer),
        server,
    )

    listen_addr = f"[::]:{settings.GRPC_PORT}"
    server.add_insecure_port(listen_addr)

    logger.info("Master Data gRPC server starting on %s", listen_addr)
    await server.start()

    try:
        await server.wait_for_termination()
    except asyncio.CancelledError:
        logger.info("Shutdown signal received — flushing Kafka producer...")
        event_producer.flush()
        logger.info("Master Data service shut down cleanly.")


if __name__ == "__main__":
    asyncio.run(serve())
