"""Kafka event producers for patient_service."""

import json
import logging
import asyncio
from aiokafka import AIOKafkaProducer
from app.core.config import settings

logger = logging.getLogger(__name__)

class EventProducer:
    """
    Manages asynchronous event broadcasting to Kafka.
    """
    def __init__(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS
        )

    async def start(self):
        """Starts the producer."""
        await self.producer.start()

    async def stop(self):
        """Stops the producer."""
        await self.producer.stop()

    def broadcast_patient_registered(self, patient_id: str, hospital_code: str, timestamp: str):
        """
        Emits a PatientRegistered event asynchronously.
        Fire-and-forget: creates a task to avoid blocking the caller.
        """
        payload = {
            "event_type": "PatientRegistered",
            "patient_id": patient_id,
            "hospital_code": hospital_code,
            "timestamp": timestamp
        }
        
        asyncio.create_task(self._send_event("patient_lifecycle", payload))
        
    async def _send_event(self, topic: str, payload: dict):
        try:
            message = json.dumps(payload).encode("utf-8")
            await self.producer.send_and_wait(topic, message)
            logger.info(f"Broadcasted to {topic}: {payload['event_type']}")
        except Exception as e:
            logger.error(f"Failed to publish event to {topic}: {e}")
