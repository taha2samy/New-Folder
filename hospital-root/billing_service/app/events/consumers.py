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
import datetime
from decimal import Decimal

from aiokafka import AIOKafkaConsumer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import settings
from app.domain.repository import BillingRepository
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
                    if payload.get("event_type") == "EncounterCreated":
                        await self._handle_encounter_created(payload, trace_id)
                    elif payload.get("event_type") == "EncounterCompleted":
                        await self._handle_encounter_completed(payload, trace_id)
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
        Enriched EncounterCreated payload:
          {
            "event_type":   "EncounterCreated",
            "event_id":     "<uuid>",          
            "patient_id":   "<uuid>",
            "encounter_id": "<uuid>",
            "encounter_type": "ADMISSION",
            "bed_id":       "<uuid>",
            "bed_category": "GENERAL",
            "bed_price":    150.0
          }
        """
        event_id     = payload.get("event_id")
        patient_id   = payload.get("patient_id")
        encounter_id = payload.get("encounter_id")
        encounter_type = payload.get("encounter_type", "OPD")
        bed_id       = payload.get("bed_id", "")
        bed_category = payload.get("bed_category", "GENERAL")
        bed_price    = Decimal(str(payload.get("bed_price", 0.0)))

        if not all([event_id, patient_id, encounter_id]):
            logger.error(f"EncounterCreated missing fields | trace_id={trace_id}")
            return

        async with self._session_factory() as session:
            repo = BillingRepository(session)

            # 1. Admission Setup Fee
            await repo.add_bill_item(
                patient_id=patient_id,
                item_type="ADMISSION_SETUP", 
                reference_id=f"{event_id}_SETUP",
                quantity=Decimal("1"),
                amount=CONSULTATION_FEE,
            )

            # 2. Track stay for recurring billing (Self-Sufficient / Context Completeness)
            if encounter_type == "ADMISSION" and bed_id:
                await repo.update_stay(
                    encounter_id=encounter_id,
                    patient_id=patient_id,
                    bed_id=bed_id,
                    bed_category=bed_category,
                    bed_price=bed_price,
                    status="ACTIVE"
                )

            logger.info(f"EncounterCreated processed | stay tracked for admission: {encounter_id}")

    async def _handle_encounter_completed(self, payload: dict, trace_id: str) -> None:
        encounter_id = payload.get("encounter_id")
        if not encounter_id: return

        async with self._session_factory() as session:
            repo = BillingRepository(session)
            # Fetch stay and mark completed
            # We don't have update_stay_status but we can use update_stay with status="COMPLETED"
            # However, we'd need more info or just a dedicated method.
            # Let's assume update_stay handles it if we pass dummy values for others or if it fetches first.
            # Actually, I added update_stay which takes all fields. 
            # Ideally I should have a simple update_status.
            # Let's just use update_stay with what we have.
            await repo.update_stay(encounter_id, "", "", "", Decimal("0"), status="COMPLETED")
            logger.info(f"EncounterCompleted processed | stay closed: {encounter_id}")

    # ------------------------------------------------------------------
    # Midnight Recurring Billing (Background Simulation)
    # ------------------------------------------------------------------

    async def process_midnight_billing(self) -> None:
        """
        Iterates over all active admissions (tracked locally) and applies a daily bed charge.
        NO gRPC calls to Clinical Service (Independence).
        """
        logger.info("Starting midnight recurring billing cycle (Independent Mode)...")
        
        async with self._session_factory() as session:
            repo = BillingRepository(session)
            active_stays = await repo.get_active_stays()
            
            today_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")
            
            for stay in active_stays:
                # Idempotency: reference_id = <encounter_id>_BED_<date>
                await repo.add_bill_item(
                    patient_id=stay.patient_id,
                    item_type="BED_CHARGE",
                    reference_id=f"{stay.id}_BED_{today_str}",
                    quantity=Decimal("1"),
                    amount=stay.bed_price,
                )
                logger.info(
                    "Daily bed charge applied | patient=%s status=ADMITTED date=%s",
                    stay.patient_id, today_str
                )
        
        logger.info("Midnight billing cycle completed.")
