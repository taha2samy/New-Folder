"""Repository layer for Clinical Encounters."""

from typing import List, Protocol
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from .models import Encounter, VitalSign, Diagnosis

class ClinicalRepositoryProtocol(Protocol):
    async def create_encounter(self, encounter: Encounter) -> Encounter: ...
    async def get_patient_encounters(self, patient_id: str, doctor_id: str, role: str) -> List[Encounter]: ...
    async def has_active_admission(self, patient_id: str) -> bool: ...
    async def get_encounter_by_id(self, encounter_id: str) -> Encounter: ...
    async def suspend_patient_encounters(self, patient_id: str) -> None: ...

class ClinicalRepository(ClinicalRepositoryProtocol):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _apply_rls(self, stmt, doctor_id: str, role: str):
        """
        Advanced RLS: ChiefOfStaff and Admin can see all encounters.
        Doctors can only see encounters they authored.
        """
        role_lower = role.lower()
        if role_lower not in ("chiefofstaff", "admin"):
            stmt = stmt.where(Encounter.doctor_id == doctor_id)
        return stmt

    async def get_patient_encounters(self, patient_id: str, doctor_id: str, role: str) -> List[Encounter]:
        stmt = select(Encounter).where(Encounter.patient_id == patient_id).options(selectinload(Encounter.diagnoses))
        stmt = self._apply_rls(stmt, doctor_id, role)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def has_active_admission(self, patient_id: str) -> bool:
        stmt = select(Encounter).where(
            and_(
                Encounter.patient_id == patient_id,
                Encounter.encounter_type == "ADMISSION",
                Encounter.status == "ACTIVE"
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().first() is not None

    async def create_encounter(self, encounter: Encounter) -> Encounter:
        self.session.add(encounter)
        return encounter

    async def get_encounter_by_id(self, encounter_id: str) -> Encounter:
        stmt = select(Encounter).where(Encounter.id == encounter_id).options(selectinload(Encounter.diagnoses))
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
