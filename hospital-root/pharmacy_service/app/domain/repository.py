"""Repository layer implementing atomic dispensing and FEFO."""

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.models import Pharmaceutical, MedicalLot, StockMovement, MovementType
from datetime import datetime

logger = logging.getLogger(__name__)

class InadequateStockError(Exception):
    pass

class PharmacyRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_pharmaceutical(self, pharma_id: str) -> Pharmaceutical:
        result = await self._session.execute(
            select(Pharmaceutical).where(Pharmaceutical.id == pharma_id)
        )
        return result.scalars().first()
        
    async def get_pharmaceutical_by_code(self, code: str) -> Pharmaceutical:
        result = await self._session.execute(
            select(Pharmaceutical).where(Pharmaceutical.code == code)
        )
        return result.scalars().first()

    async def create_pharmaceutical(self, pharma: Pharmaceutical) -> Pharmaceutical:
        self._session.add(pharma)
        return pharma

    async def get_total_stock(self, pharma_id: str) -> int:
        result = await self._session.execute(
            select(MedicalLot)
            .where(MedicalLot.pharmaceutical_id == pharma_id)
            .where(MedicalLot.quantity > 0)
        )
        lots = result.scalars().all()
        return sum(lot.quantity for lot in lots)

    async def add_stock(self, pharma_id: str, lot_code: str, expiry_date: datetime, quantity: int, unit_cost: float, user_id: str) -> MedicalLot:
        # Check if lot exists
        result = await self._session.execute(
            select(MedicalLot).where(MedicalLot.lot_code == lot_code)
        )
        lot = result.scalars().first()
        if lot:
            lot.quantity += quantity
        else:
            lot = MedicalLot(
                pharmaceutical_id=pharma_id,
                lot_code=lot_code,
                expiry_date=expiry_date,
                quantity=quantity,
                unit_cost=unit_cost
            )
            self._session.add(lot)
            await self._session.flush() # Ensure lot has an ID

        movement = StockMovement(
            lot_id=lot.id,
            type=MovementType.CHARGE,
            quantity=quantity,
            user_id=user_id
        )
        self._session.add(movement)
        return lot

    async def dispense_medicine(self, pharma_id: str, quantity_to_dispense: int, patient_id: str, user_id: str) -> list[dict]:
        """
        Implements Atomic Dispensing via FEFO (First Expired, First Out).
        Returns a list of dicts with dispensing details for billing:
        [{'lot_id': str, 'quantity': int, 'unit_cost': float}]
        """
        total_available = await self.get_total_stock(pharma_id)
        if total_available < quantity_to_dispense:
            raise InadequateStockError(f"Requested {quantity_to_dispense}, but only {total_available} available.")

        # Find lots with quantity > 0, ordered by nearest expiry date
        result = await self._session.execute(
            select(MedicalLot)
            .where(MedicalLot.pharmaceutical_id == pharma_id)
            .where(MedicalLot.quantity > 0)
            .order_by(MedicalLot.expiry_date.asc())
        )
        lots = result.scalars().all()

        remaining_to_dispense = quantity_to_dispense
        dispensed_details = []

        # Iterate lots and deduct sequentially
        for lot in lots:
            if remaining_to_dispense <= 0:
                break

            deduction = min(remaining_to_dispense, lot.quantity)
            lot.quantity -= deduction
            remaining_to_dispense -= deduction

            # Record movement
            movement = StockMovement(
                lot_id=lot.id,
                type=MovementType.DISCHARGE,
                quantity=deduction,
                patient_id=patient_id,
                user_id=user_id
            )
            self._session.add(movement)
            dispensed_details.append({
                "lot_id": lot.id,
                "quantity": deduction,
                "unit_cost": lot.unit_cost
            })

        if remaining_to_dispense > 0:
            # Should theoretically never hit this due to `get_total_stock` check
            # but serves as a safety guard within the transaction
            raise InadequateStockError("Critical error during dispensing calculation.")

        return dispensed_details
