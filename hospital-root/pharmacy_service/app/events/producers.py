"""Event producers for pharmacy_service.

Publishes to hospital.pharmacy.dispensing so the billing_service consumer
can process MedicineDispensed events and apply charges.
"""

import json
import logging
import uuid
from decimal import Decimal
from datetime import datetime, timezone

from confluent_kafka import Producer
from app.core.config import settings

logger = logging.getLogger(__name__)

TOPIC_MEDICINE_DISPENSED = "hospital.pharmacy.dispensing"


class PharmacyEventProducer:
    def __init__(self) -> None:
        self._producer = Producer({
            "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
            "client.id": "pharmacy-event-producer",
        })

    # ------------------------------------------------------------------
    # Public broadcast methods
    # ------------------------------------------------------------------

    def broadcast_medicine_dispensed(
        self,
        patient_id: str,
        medical_id: str,
        quantity_dispensed: int,
        unit_cost: Decimal,
        actor_id: str,
        trace_id: str = "",
    ) -> None:
        """
        Emit a MedicineDispensed event on hospital.pharmacy.dispensing.

        The event_id is a new UUID per call — it serves as the idempotency key
        for the billing_service consumer.
        """
        event_id = str(uuid.uuid4())
        total_cost = float(unit_cost * quantity_dispensed)

        payload = {
            "event_type": "MedicineDispensed",
            "event_id": event_id,
            "patient_id": patient_id,
            "medicine_id": medical_id,
            "quantity": quantity_dispensed,
            "unit_cost": float(unit_cost),
            "total_cost": total_cost,
            "actor_id": actor_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trace_id": trace_id,
        }

        headers = []
        if trace_id:
            headers.append(("x-trace-id", trace_id.encode("utf-8")))

        self._producer.produce(
            topic=TOPIC_MEDICINE_DISPENSED,
            key=patient_id.encode("utf-8"),
            value=json.dumps(payload).encode("utf-8"),
            headers=headers,
            callback=self._delivery_report,
        )
        self._producer.poll(0)
        logger.info(
            "MedicineDispensed event queued | event_id=%s patient=%s medical=%s qty=%d total=%.2f",
            event_id, patient_id, medical_id, quantity_dispensed, total_cost,
        )

    def flush(self) -> None:
        """Block until all outstanding messages are delivered."""
        pending = self._producer.flush(timeout=10)
        if pending:
            logger.warning("%d messages were not delivered before flush timeout.", pending)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _delivery_report(err, msg) -> None:
        if err is not None:
            logger.error("Kafka delivery failed | topic=%s error=%s", msg.topic(), err)
        else:
            logger.debug(
                "Kafka delivery ok | topic=%s partition=%d offset=%d",
                msg.topic(), msg.partition(), msg.offset(),
            )
