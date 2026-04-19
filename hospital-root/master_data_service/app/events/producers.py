"""Kafka event producer for master_data_service.

Broadcasts ReferenceDataChanged events so that downstream services
(e.g. clinical_service) can invalidate their local caches.
"""

import json
import logging
from datetime import datetime

from confluent_kafka import Producer

from app.core.config import settings

logger = logging.getLogger(__name__)

_TOPIC_REFERENCE_DATA_CHANGED = "ReferenceDataChanged"


class MasterDataEventProducer:
    """Wraps a confluent-kafka synchronous Producer for fire-and-forget event emission."""

    def __init__(self) -> None:
        conf = {
            "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
            "client.id": "master-data-event-producer",
        }
        self._producer = Producer(conf)

    # ------------------------------------------------------------------
    # Public broadcast methods
    # ------------------------------------------------------------------

    def broadcast_reference_data_changed(
        self,
        entity_type: str,
        action: str,
        admin_id: str,
        entity_id: str,
    ) -> None:
        """
        Publish a ReferenceDataChanged event.

        Parameters
        ----------
        entity_type:
            Human-readable entity name, e.g. ``"WARD"`` or ``"DISEASE"``.
        action:
            One of ``"CREATE"`` or ``"UPDATE"``.
        admin_id:
            Identifier of the administrator who triggered the change.
        entity_id:
            Primary key of the modified record for targeted cache invalidation.
        """
        payload = {
            "entity_type": entity_type,
            "action":      action,
            "admin_id":    admin_id,
            "entity_id":   entity_id,
            "timestamp":   datetime.utcnow().isoformat(),
        }
        self._publish(
            topic=_TOPIC_REFERENCE_DATA_CHANGED,
            key=entity_type,
            payload=payload,
        )

    def flush(self) -> None:
        """Block until all in-flight messages have been delivered or timed out."""
        self._producer.flush()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _delivery_report(self, err, msg) -> None:
        if err is not None:
            logger.error(
                "Kafka delivery failure on topic '%s': %s", msg.topic(), err
            )
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
