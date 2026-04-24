"""
pharmacy_service — main bootstrap.

Initialises the async SQLAlchemy engine, wires the AuthInterceptor and the
PharmacyServiceHandler into an async gRPC server, and starts the event
producer. Handles SIGTERM/SIGINT for graceful shutdown.
"""

import asyncio
import logging
import signal

import grpc
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.grpc.handler import PharmacyServiceHandler
from app.grpc.interceptors import AuthInterceptor
from app.events.producers import PharmacyEventProducer
from app.generated import pharmacy_pb2_grpc

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


def build_session_factory() -> async_sessionmaker[AsyncSession]:
    """Create the async engine and return a bound session factory."""
    engine = create_async_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        echo=False,
    )
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def serve() -> None:
    session_factory = build_session_factory()
    event_producer = PharmacyEventProducer()

    server = grpc.aio.server(interceptors=[AuthInterceptor()])
    pharmacy_pb2_grpc.add_PharmacyServiceServicer_to_server(
        PharmacyServiceHandler(session_factory, event_producer),
        server,
    )

    listen_addr = f"[::]:{settings.GRPC_PORT}"
    server.add_insecure_port(listen_addr)
    await server.start()
    logger.info("Pharmacy gRPC server listening on %s", listen_addr)

    async def _shutdown():
        logger.info("Graceful shutdown initiated…")
        await server.stop(grace=5)
        event_producer.flush()
        logger.info("Pharmacy service stopped.")

    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGTERM, lambda: asyncio.create_task(_shutdown()))
    loop.add_signal_handler(signal.SIGINT,  lambda: asyncio.create_task(_shutdown()))

    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(serve())
