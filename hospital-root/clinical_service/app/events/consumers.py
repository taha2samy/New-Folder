"""Kafka consumers for clinical_service."""

import json
import logging
import asyncio
from aiokafka import AIOKafkaConsumer
from app.core.config import settings
from app.domain.repository import ClinicalRepository

logger = logging.getLogger(__name__)

class PatientEventConsumer:
    def __init__(self, db_session_factory):
        self.consumer = AIOKafkaConsumer(
            "patient_lifecycle",
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id="clinical_service_group"
        )
        self.db_session_factory = db_session_factory
        self._running = False

    async def start(self):
        await self.consumer.start()
        self._running = True
        logger.info("Kafka Consumer started for Patient events.")
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
                if payload.get("event_type") == "PatientDeleted":
                    patient_id = payload.get("patient_id")
                    if patient_id:
                        await self._handle_patient_deleted(patient_id)
        except Exception as e:
            logger.error(f"Consumer loop error: {e}")

    async def _handle_patient_deleted(self, patient_id: str):
        logger.warning(f"Suspending active encounters for deleted patient {patient_id}")
        try:
            async with self.db_session_factory() as session:
                repo = ClinicalRepository(session)
                await repo.suspend_patient_encounters(patient_id)
                await session.commit()
        except Exception as e:
            logger.error(f"Failed to process PatientDeleted for {patient_id}: {e}")
