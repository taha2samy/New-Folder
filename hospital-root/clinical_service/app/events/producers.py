"""Kafka producers for clinical_service."""

import json
import logging
import asyncio
from aiokafka import AIOKafkaProducer
from app.core.config import settings

logger = logging.getLogger(__name__)

class EncounterEventProducer:
    def __init__(self):
        self.producer = AIOKafkaProducer(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS)

    async def start(self): await self.producer.start()
    async def stop(self):  await self.producer.stop()

    def broadcast_encounter_created(self, encounter_id: str, patient_id: str, encounter_type: str, bed_id: str = "", bed_category: str = "", ward_id: str = "", bed_price: float = 0.0):
        import uuid
        payload = {
            "event_id": str(uuid.uuid4()),
            "event_type": "EncounterCreated",
            "encounter_id": encounter_id,
            "patient_id": patient_id,
            "encounter_type": encounter_type,
            "bed_id": bed_id,
            "bed_category": bed_category,
            "ward_id": ward_id,
            "bed_price": bed_price
        }
        asyncio.create_task(self._send_event("hospital.clinical.encounters", payload))

    def broadcast_encounter_completed(self, encounter_id: str, patient_id: str):
        import uuid
        payload = {
            "event_id": str(uuid.uuid4()),
            "event_type": "EncounterCompleted",
            "encounter_id": encounter_id,
            "patient_id": patient_id
        }
        asyncio.create_task(self._send_event("hospital.clinical.encounters", payload))

    def broadcast_bed_status_changed(self, bed_id: str, status: str, ward_id: str):
        import uuid
        payload = {
            "event_id": str(uuid.uuid4()),
            "event_type": "BedStatusChanged",
            "bed_id": bed_id,
            "status": status,
            "ward_id": ward_id
        }
        asyncio.create_task(self._send_event("hospital.clinical.lifecycle", payload))

    async def _send_event(self, topic: str, payload: dict):
        try:
            msg = json.dumps(payload).encode("utf-8")
            await self.producer.send_and_wait(topic, msg)
        except Exception as e:
            logger.error(f"Failed to publish event to {topic}: {e}")
