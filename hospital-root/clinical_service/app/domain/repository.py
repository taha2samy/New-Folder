"""Repository layer for Clinical Encounters."""

from typing import List, Protocol
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from .models import Encounter, VitalSign, Diagnosis

class ClinicalRepositoryProtocol(Protocol):
    async def create_encounter(self, encounter: Encounter) -> Encounter: ...
    async def get_patient_encounters(self, patient_id: str) -> List[Encounter]: ...
    async def has_active_admission(self, patient_id: str) -> bool: ...
    async def get_encounter_by_id(self, encounter_id: str) -> Encounter: ...
    async def suspend_patient_encounters(self, patient_id: str) -> None: ...

class ClinicalRepository(ClinicalRepositoryProtocol):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def is_bed_occupied(self, ward_id: str, bed_id: str) -> bool:
        """
        Checks if a bed is occupied in a specific ward (local check)
        """
        stmt = select(Encounter).where(
            and_(
                Encounter.ward_id == ward_id,
                Encounter.bed_id == bed_id,
                Encounter.status == "ACTIVE",      # The bed is occupied only if the status is active
                Encounter.is_deleted == False      # and the record is not deleted
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().first() is not None


    def _apply_rls(self, stmt):
        """
        Global Filter: Enforce soft delete pattern. Role-based filtering is disabled.
        """
        stmt = stmt.where(Encounter.is_deleted == False)
        return stmt

    async def get_patient_encounters(self, patient_id: str) -> List[Encounter]:
        stmt = select(Encounter).where(Encounter.patient_id == patient_id).options(
            selectinload(Encounter.diagnoses),
            selectinload(Encounter.vitals)
        )
        stmt = self._apply_rls(stmt)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def has_active_admission(self, patient_id: str) -> bool:
        stmt = select(Encounter).where(
            and_(
                Encounter.patient_id == patient_id,
                Encounter.encounter_type == "ADMISSION",
                Encounter.status == "ACTIVE",
                Encounter.is_deleted == False
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().first() is not None

    async def get_active_admissions(self) -> List[Encounter]:
        """Return all active admissions."""
        stmt = select(Encounter).where(
            and_(
                Encounter.encounter_type == "ADMISSION",
                Encounter.status == "ACTIVE",
                Encounter.is_deleted == False
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_encounter(self, encounter: Encounter) -> Encounter:
        self.session.add(encounter)
        return encounter

    async def get_encounter_by_id(self, encounter_id: str) -> Encounter:
        stmt = select(Encounter).where(
            and_(
                Encounter.id == encounter_id,
                Encounter.is_deleted == False
            )
        ).options(
            selectinload(Encounter.diagnoses),
            selectinload(Encounter.vitals)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def suspend_patient_encounters(self, patient_id: str) -> None:
        """Suspends all active encounters for a deleted patient."""
        stmt = update(Encounter).where(
            and_(
                Encounter.patient_id == patient_id,
                Encounter.status == "ACTIVE"
            )
        ).values(status="SUSPENDED")
        await self.session.execute(stmt)
