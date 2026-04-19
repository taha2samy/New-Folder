"""Kafka event producers for laboratory_service.

Two events are broadcast:

* LabRequestCreated  – published when a new test request is created so that
                       the billing_service can charge the patient.
* LabResultCompleted – published when a technician submits results so that the
                       notification_service can alert the requesting clinician.
"""

import json
import logging
from datetime import datetime

from confluent_kafka import Producer

from app.core.config import settings

logger = logging.getLogger(__name__)

_TOPIC_LAB_REQUEST_CREATED  = "LabRequestCreated"
_TOPIC_LAB_RESULT_COMPLETED = "LabResultCompleted"


class LaboratoryEventProducer:
    """Wraps a confluent-kafka synchronous Producer for fire-and-forget event emission."""

    def __init__(self) -> None:
        conf = {
            "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
            "client.id": "laboratory-event-producer",
        }
        self._producer = Producer(conf)

    # ------------------------------------------------------------------
    # Public broadcast methods
    # ------------------------------------------------------------------

    def broadcast_lab_request_created(
        self,
        patient_id: str,
        exam_type_id: str,
        request_id: str,
    ) -> None:
        """
        Publish a LabRequestCreated event.

        Consumed by billing_service to create a BillItem for the examination fee.
        """
        payload = {
            "patient_id":   patient_id,
            "exam_type_id": exam_type_id,
            "request_id":   request_id,
            "timestamp":    datetime.utcnow().isoformat(),
        }
        self._publish(_TOPIC_LAB_REQUEST_CREATED, key=patient_id, payload=payload)

    def broadcast_lab_result_completed(
        self,
        patient_id: str,
        request_id: str,
        exam_type_id: str,
        technician_id: str,
    ) -> None:
        """
        Publish a LabResultCompleted event.

        Consumed by notification_service to alert the ordering clinician or patient.
        """
        payload = {
            "patient_id":    patient_id,
            "request_id":    request_id,
            "exam_type_id":  exam_type_id,
            "technician_id": technician_id,
            "timestamp":     datetime.utcnow().isoformat(),
        }
        self._publish(_TOPIC_LAB_RESULT_COMPLETED, key=patient_id, payload=payload)

    def flush(self) -> None:
        """Block until all in-flight messages have been delivered or timed out."""
        self._producer.flush()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _delivery_report(self, err, msg) -> None:
        if err is not None:
            logger.error("Kafka delivery failure on topic '%s': %s", msg.topic(), err)
        else:
            logger.debug(
                "Event delivered — topic: %s, partition: %d, offset: %d",
                msg.topic(),
                msg.partition(),
                msg.offset(),
            )

    def _publish(self, topic: str, key: str, payload: dict) -> None:
        """Serialise payload to JSON and enqueue the message for delivery."""
        self._producer.produce(
            topic,
            key=key.encode("utf-8"),
            value=json.dumps(payload).encode("utf-8"),
            callback=self._delivery_report,
        )
        self._producer.poll(0)   # Trigger delivery callbacks without blocking
