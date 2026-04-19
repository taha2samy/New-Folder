"""Event producers for Pharmacy Service."""

import json
import logging
from confluent_kafka import Producer
from app.core.config import settings
from datetime import datetime

logger = logging.getLogger(__name__)

class PharmacyEventProducer:
    def __init__(self):
        conf = {
            'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
            'client.id': 'pharmacy-event-producer'
        }
        self.producer = Producer(conf)
        self.topic = "MedicineDispensed"

    def _delivery_report(self, err, msg):
        if err is not None:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}]")

    def broadcast_medicine_dispensed(
        self, 
        patient_id: str, 
        medical_id: str, 
        quantity_dispensed: int, 
        unit_cost: float,
        actor_id: str
    ):
        event_payload = {
            "patient_id": patient_id,
            "medical_id": medical_id,
            "quantity_dispensed": quantity_dispensed,
            "unit_cost": unit_cost,
            "actor_id": actor_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.producer.produce(
            self.topic,
            key=patient_id.encode('utf-8'),
            value=json.dumps(event_payload).encode('utf-8'),
            callback=self._delivery_report
        )
        self.producer.poll(0)

    def flush(self):
        self.producer.flush()
