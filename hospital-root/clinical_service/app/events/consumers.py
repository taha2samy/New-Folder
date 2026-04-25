"""Kafka consumers for clinical_service."""

import json
import logging
import asyncio
from aiokafka import AIOKafkaConsumer
from app.core.config import settings
from app.domain.repository import ClinicalRepository

from app.core.config import settings
from app.generated import master_data_pb2

logger = logging.getLogger(__name__)

class PatientEventConsumer:
    def __init__(self, db_session_factory, master_data_client, event_producer):
        self.consumer = AIOKafkaConsumer(
            "patient_lifecycle",
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id="clinical_service_group"
        )
        self.db_session_factory = db_session_factory
        self.master_data_client = master_data_client
        self.event_producer = event_producer
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
        logger.warning(f"Patient {patient_id} deleted. Cleaning up clinical resources.")
        try:
            async with self.db_session_factory() as session:
                repo = ClinicalRepository(session)
                
                # 1. Find if patient has an active admission
                active_adm = await repo.get_active_admission(patient_id)
                
                # 2. Suspend all active encounters
                # 3. If they had a bed, free it (Event-Driven / No Backdoor / Natural Flow)
                if active_adm and active_adm.bed_id:
                    logger.info(f"Freeing bed {active_adm.bed_id} for deleted patient {patient_id} via Fat Event.")
                    
                    # Moving bed to CLEANING as per ERP standard housekeeping flow
                    self.event_producer.broadcast_bed_status_changed(
                        bed_id=active_adm.bed_id, 
                        status="CLEANING", 
                        ward_id=active_adm.ward_id or "unknown"
                    )

        except Exception as e:
            logger.error(f"Failed to process PatientDeleted for {patient_id}: {e}")
