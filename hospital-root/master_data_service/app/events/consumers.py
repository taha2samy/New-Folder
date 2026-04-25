import json
import logging
import asyncio
from aiokafka import AIOKafkaConsumer
from app.core.config import settings
from app.domain.repository import MasterDataRepository
from app.generated import master_data_pb2

logger = logging.getLogger(__name__)

class BedEventConsumer:
    def __init__(self, db_session_factory):
        self.consumer = AIOKafkaConsumer(
            "hospital.clinical.lifecycle",
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id="master_data_service_group"
        )
        self.db_session_factory = db_session_factory
        self._running = False

    async def start(self):
        await self.consumer.start()
        self._running = True
        logger.info("Master Data Consumer started for Bed Lifecycle events.")
        asyncio.create_task(self._consume_loop())

    async def stop(self):
        self._running = False
        await self.consumer.stop()

    async def _consume_loop(self):
        try:
            async for msg in self.consumer:
                if not self._running:
                    break
                payload = json.loads(msg.value.decode("utf-8"))
                if payload.get("event_type") == "BedStatusChanged":
                    await self._handle_bed_status_changed(payload)
        except Exception as e:
            logger.error(f"Master Data Consumer loop error: {e}")

    async def _handle_bed_status_changed(self, payload: dict):
        bed_id = payload.get("bed_id")
        status_name = payload.get("status") # AVAILABLE, OCCUPIED, CLEANING
        
        # Map string status to enum if needed, or repository handles it
        status_map = {
            "AVAILABLE": master_data_pb2.BedStatus.AVAILABLE,
            "OCCUPIED": master_data_pb2.BedStatus.OCCUPIED,
            "CLEANING": master_data_pb2.BedStatus.CLEANING,
            "MAINTENANCE": master_data_pb2.BedStatus.MAINTENANCE
        }
        status_enum = status_map.get(status_name, master_data_pb2.BedStatus.AVAILABLE)

        logger.info(f"Syncing Bed {bed_id} status to {status_name} from event.")
        
        try:
            async with self.db_session_factory() as session:
                repo = MasterDataRepository(session)
                await repo.update_bed_status(bed_id, status_enum)
                await session.commit()
        except Exception as e:
            logger.error(f"Failed to sync bed status for {bed_id}: {e}")
