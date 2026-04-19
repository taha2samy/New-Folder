"""
billing_service — Kafka event consumer.

Listens on:
  - hospital.clinical.encounters   (EncounterCreated events)
  - hospital.pharmacy.dispensing   (MedicineDispensed events)

Financial processing rules:
  - MedicineDispensed : look up PriceList by (DRUG, medicine_id)
                        ➜ get_or_create Bill ➜ add BillItem
  - EncounterCreated  : add a flat CONSULTATION_FEE BillItem

Idempotency:
  reference_id stored in BillItem is the Kafka event_id so duplicate
  deliveries are silently skipped by the repository's pre-insert check.
"""

import asyncio
import json
import logging
from decimal import Decimal

from aiokafka import AIOKafkaConsumer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import settings
from app.domain.repository import BillingRepository

logger = logging.getLogger(__name__)

TOPICS = [
    "hospital.clinical.encounters",
    "hospital.pharmacy.dispensing",
]

# Default consultation fee charged whenever an encounter is opened.
CONSULTATION_FEE = Decimal("50.00")

# Fallback price when medicine_id is not found in PriceList.
DEFAULT_DRUG_PRICE = Decimal("0.00")


class BillingEventConsumer:
    """Async Kafka consumer that drives the billing workflow."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._consumer: AIOKafkaConsumer | None = None
        self._running = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def run(self) -> None:
        """Start consuming. Blocks until stop() is called."""
        self._consumer = AIOKafkaConsumer(
            *TOPICS,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id="billing_service_group",
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            value_deserializer=lambda raw: json.loads(raw.decode("utf-8")),
        )
        await self._consumer.start()
        self._running = True
        logger.info(
            "Kafka consumer started — topics: %s | brokers: %s",
            TOPICS,
            settings.KAFKA_BOOTSTRAP_SERVERS,
        )
        try:
            await self._consume_loop()
        finally:
            await self._consumer.stop()
            logger.info("Kafka consumer stopped.")

    async def stop(self) -> None:
        """Signal the consume loop to exit cleanly."""
        self._running = False
        if self._consumer:
            await self._consumer.stop()

    # ------------------------------------------------------------------
    # Internal consume loop
    # ------------------------------------------------------------------

    async def _consume_loop(self) -> None:
        async for msg in self._consumer:
            if not self._running:
                break

            trace_id = "unknown"
            if msg.headers:
                headers = dict(msg.headers)
                trace_id = (headers.get(b"x-trace-id") or b"unknown").decode("utf-8")

            topic = msg.topic
            payload: dict = msg.value

            logger.info(
                "Received message | topic=%s trace_id=%s event_type=%s",
                topic,
                trace_id,
                payload.get("event_type", "—"),
            )

            try:
                if topic == "hospital.pharmacy.dispensing":
                    await self._handle_medicine_dispensed(payload, trace_id)
                elif topic == "hospital.clinical.encounters":
                    await self._handle_encounter_created(payload, trace_id)
                else:
                    logger.warning("Unhandled topic: %s", topic)
            except Exception as exc:
                logger.exception(
                    "Error processing message | topic=%s trace_id=%s error=%s",
                    topic,
                    trace_id,
                    exc,
                )

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    async def _handle_medicine_dispensed(self, payload: dict, trace_id: str) -> None:
        """
        Expected payload shape:
          {
            "event_type": "MedicineDispensed",
            "event_id":   "<uuid>",          # idempotency key
            "patient_id": "<uuid>",
            "medicine_id":"<uuid>",
            "quantity":    1
          }
        """
        event_type = payload.get("event_type", "")
        if event_type != "MedicineDispensed":
            return

        event_id   = payload.get("event_id")
        patient_id = payload.get("patient_id")
        medicine_id = payload.get("medicine_id")
        quantity   = Decimal(str(payload.get("quantity", 1)))

        if not all([event_id, patient_id, medicine_id]):
            logger.error(
                "MedicineDispensed payload missing required fields | trace_id=%s payload=%s",
                trace_id, payload,
            )
            return

        async with self._session_factory() as session:
            repo = BillingRepository(session)

            # Look up unit price; fall back to zero so the item is still recorded.
            unit_price = await repo.get_price("DRUG", medicine_id) or DEFAULT_DRUG_PRICE
            amount = unit_price * quantity

            result = await repo.add_bill_item(
                patient_id=patient_id,
                item_type="DRUG",
                reference_id=event_id,   # event_id as idempotency key
                quantity=quantity,
                amount=amount,
            )
            if result is None:
                logger.info(
                    "Duplicate MedicineDispensed skipped | event_id=%s trace_id=%s",
                    event_id, trace_id,
                )
            else:
                logger.info(
                    "Bill item added | patient=%s medicine=%s amount=%s trace_id=%s",
                    patient_id, medicine_id, amount, trace_id,
                )

    async def _handle_encounter_created(self, payload: dict, trace_id: str) -> None:
        """
        Expected payload shape:
          {
            "event_type":   "EncounterCreated",
            "event_id":     "<uuid>",          # idempotency key
            "patient_id":   "<uuid>",
            "encounter_id": "<uuid>"
          }
        """
        event_type = payload.get("event_type", "")
        if event_type != "EncounterCreated":
            return

        event_id     = payload.get("event_id")
        patient_id   = payload.get("patient_id")
        encounter_id = payload.get("encounter_id")

        if not all([event_id, patient_id, encounter_id]):
            logger.error(
                "EncounterCreated payload missing required fields | trace_id=%s payload=%s",
                trace_id, payload,
            )
            return

        async with self._session_factory() as session:
            repo = BillingRepository(session)

            result = await repo.add_bill_item(
                patient_id=patient_id,
                item_type="CONSULTATION",
                reference_id=event_id,  # event_id as idempotency key
                quantity=Decimal("1"),
                amount=CONSULTATION_FEE,
            )
            if result is None:
                logger.info(
                    "Duplicate EncounterCreated skipped | event_id=%s trace_id=%s",
                    event_id, trace_id,
                )
            else:
                logger.info(
                    "Consultation fee added | patient=%s encounter=%s amount=%s trace_id=%s",
                    patient_id, encounter_id, CONSULTATION_FEE, trace_id,
                )
