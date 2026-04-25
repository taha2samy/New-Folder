"""
billing_service — main bootstrap.

Runs two concurrent async tasks:
  1. gRPC server  (BillingService on GRPC_PORT)
  2. Kafka consumer  (hospital.clinical.encounters + hospital.pharmacy.dispensing)
"""

import asyncio
import logging
import signal

import grpc
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.grpc.handler import BillingServiceHandler
from app.grpc.interceptors import JWTInterceptor
from app.events.consumers import BillingEventConsumer
from app.generated import billing_pb2_grpc

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


def build_session_factory() -> async_sessionmaker[AsyncSession]:
    """Create the async SQLAlchemy engine and return a session factory."""
    engine = create_async_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        echo=False,
    )
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def serve_grpc(session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Start the async gRPC server and block until stopped."""
    server = grpc.aio.server(interceptors=[JWTInterceptor()])
    handler = BillingServiceHandler(session_factory)
    billing_pb2_grpc.add_BillingServiceServicer_to_server(handler, server)

    listen_addr = f"[::]:{settings.GRPC_PORT}"
    server.add_insecure_port(listen_addr)
    await server.start()
    logger.info("gRPC BillingService listening on %s", listen_addr)

    async def _graceful_shutdown():
        logger.info("Shutting down gRPC server…")
        await server.stop(grace=5)

    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGTERM, lambda: asyncio.create_task(_graceful_shutdown()))
    loop.add_signal_handler(signal.SIGINT,  lambda: asyncio.create_task(_graceful_shutdown()))

    await server.wait_for_termination()


async def run_recurring_billing_cycle(consumer: BillingEventConsumer) -> None:
    """Simple background loop to trigger midnight billing every 24 hours."""
    # Optional: sleep until next midnight if we want real-world behavior
    while True:
        try:
            logger.info("Recurring billing loop: Sleeping for 24 hours...")
            await asyncio.sleep(24 * 3600)
            logger.info("Recurring billing loop: Triggering midnight cycle.")
            await consumer.process_midnight_billing()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("Error in recurring billing loop: %s", e)
            await asyncio.sleep(600) # Retry in 10 mins


async def main() -> None:
    session_factory = build_session_factory()
    consumer = BillingEventConsumer(session_factory)

    logger.info("Starting BillingService…")
    try:
        await asyncio.gather(
            serve_grpc(session_factory),
            consumer.run(),
            run_recurring_billing_cycle(consumer),
        )
    finally:
        await consumer.stop()
        logger.info("BillingService shut down cleanly.")


if __name__ == "__main__":
    asyncio.run(main())
