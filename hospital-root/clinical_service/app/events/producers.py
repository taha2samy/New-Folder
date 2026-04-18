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

    def broadcast_encounter_created(self, encounter_id: str, patient_id: str, encounter_type: str):
        payload = {
            "event_type": "EncounterCreated",
            "encounter_id": encounter_id,
            "patient_id": patient_id,
            "encounter_type": encounter_type
        }
        asyncio.create_task(self._send_event("clinical_lifecycle", payload))

    def broadcast_encounter_completed(self, encounter_id: str, patient_id: str):
        payload = {
            "event_type": "EncounterCompleted",
            "encounter_id": encounter_id,
            "patient_id": patient_id
        }
        asyncio.create_task(self._send_event("clinical_lifecycle", payload))

    async def _send_event(self, topic: str, payload: dict):
        try:
            msg = json.dumps(payload).encode("utf-8")
            await self.producer.send_and_wait(topic, msg)
        except Exception as e:
            logger.error(f"Failed to publish event to {topic}: {e}")
