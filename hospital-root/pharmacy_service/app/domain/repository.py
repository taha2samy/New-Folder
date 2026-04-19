"""Repository layer implementing atomic dispensing with FEFO (First Expired, First Out)."""

import logging
from decimal import Decimal
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.domain.models import Pharmaceutical, MedicalLot, StockMovement, MovementType

logger = logging.getLogger(__name__)


class InadequateStockError(Exception):
    """Raised when requested dispensing quantity exceeds available stock."""


class PharmacyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Pharmaceutical queries
    # ------------------------------------------------------------------

    async def get_pharmaceutical(self, pharma_id: str) -> Pharmaceutical | None:
        result = await self._session.execute(
            select(Pharmaceutical)
            .where(Pharmaceutical.id == pharma_id)
            .where(Pharmaceutical.is_deleted == False)
        )
        return result.scalars().first()

    async def get_pharmaceutical_by_code(self, code: str) -> Pharmaceutical | None:
        result = await self._session.execute(
            select(Pharmaceutical)
            .where(Pharmaceutical.code == code)
            .where(Pharmaceutical.is_deleted == False)
        )
        return result.scalars().first()

    # ------------------------------------------------------------------
    # Stock queries
    # ------------------------------------------------------------------

    async def get_total_stock(self, pharma_id: str) -> int:
        result = await self._session.execute(
            select(MedicalLot)
            .where(MedicalLot.medical_id == pharma_id)
            .where(MedicalLot.is_deleted == False)
            .where(MedicalLot.quantity > 0)
        )
        lots = result.scalars().all()
        return sum(lot.quantity for lot in lots)

    # ------------------------------------------------------------------
    # Stock mutation — Add Stock (CHARGE movement)
    # ------------------------------------------------------------------

    async def add_stock(
        self,
        pharma_id: str,
        lot_code: str,
        expiry_date: datetime,
        quantity: int,
        unit_cost: Decimal,
        actor_id: str,
    ) -> MedicalLot:
        """Create or top-up a MedicalLot, then record a CHARGE movement."""
        result = await self._session.execute(
            select(MedicalLot)
            .where(MedicalLot.lot_code == lot_code)
            .where(MedicalLot.is_deleted == False)
        )
        lot = result.scalars().first()

        if lot:
            lot.quantity += quantity
        else:
            lot = MedicalLot(
                medical_id=pharma_id,
                lot_code=lot_code,
                expiry_date=expiry_date,
                quantity=quantity,
                unit_cost=unit_cost,
            )
            self._session.add(lot)
            await self._session.flush()   # ensure lot.id is populated

        movement = StockMovement(
            medical_id=pharma_id,
            lot_id=lot.id,
            type=MovementType.CHARGE,
            quantity=quantity,
            actor_id=actor_id,
        )
        self._session.add(movement)
        return lot

    # ------------------------------------------------------------------
    # Stock mutation — Dispense (FEFO DISCHARGE movements)
    # ------------------------------------------------------------------

    async def dispense_medicine(
        self,
        pharma_id: str,
        quantity_to_dispense: int,
        patient_id: str,
        actor_id: str,
    ) -> list[dict]:
        """
        Atomically dispense stock using FEFO ordering.

        Iterates lots sorted by expiry_date ascending (nearest expiry first)
        and deducts from each until the requested quantity is fulfilled.

        Returns a list of dicts:
          [{"lot_id": str, "quantity": int, "unit_cost": Decimal}]

        Raises:
          InadequateStockError if total available stock is less than requested.
        """
        total_available = await self.get_total_stock(pharma_id)
        if total_available < quantity_to_dispense:
            raise InadequateStockError(
                f"Requested {quantity_to_dispense} units but only {total_available} available."
            )

        # FEFO: fetch all available lots ordered by nearest expiry first
        result = await self._session.execute(
            select(MedicalLot)
            .where(MedicalLot.medical_id == pharma_id)
            .where(MedicalLot.is_deleted == False)
            .where(MedicalLot.quantity > 0)
            .order_by(MedicalLot.expiry_date.asc())
        )
        lots = result.scalars().all()

        remaining = quantity_to_dispense
        dispensed_details: list[dict] = []

        for lot in lots:
            if remaining <= 0:
                break

            deduction = min(remaining, lot.quantity)
            lot.quantity -= deduction
            remaining -= deduction

            movement = StockMovement(
                medical_id=pharma_id,
                lot_id=lot.id,
                type=MovementType.DISCHARGE,
                quantity=deduction,
                patient_id=patient_id,
                actor_id=actor_id,
            )
            self._session.add(movement)
            dispensed_details.append({
                "lot_id": lot.id,
                "quantity": deduction,
                "unit_cost": Decimal(str(lot.unit_cost)),
            })

        # Safety guard: should never trigger given the pre-check above
        if remaining > 0:
            raise InadequateStockError("Critical: dispensing calculation mismatch.")

        return dispensed_details

    # ------------------------------------------------------------------
    # History queries
    # ------------------------------------------------------------------

    async def get_patient_medications(self, patient_id: str) -> list[StockMovement]:
        result = await self._session.execute(
            select(StockMovement)
            .options(joinedload(StockMovement.lot))
            .where(StockMovement.patient_id == patient_id)
            .where(StockMovement.type == MovementType.DISCHARGE)
            .order_by(StockMovement.date.desc())
        )
        return result.scalars().all()
