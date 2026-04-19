"""Repository layer for patient_service with RLS integration."""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Patient

class PatientRepository:
    """
    Data access layer for Patient entities enforcing Soft Delete and RLS.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    def _apply_rls(self, stmt, user_role: str, user_id: str):
        """
        Applies Row-Level Security and Soft Delete constraints.
        If user_role is 'Patient', restrict to id == user_id.
        """
        stmt = stmt.where(Patient.is_deleted == False)
        if user_role.lower() == "patient":
            stmt = stmt.where(Patient.id == user_id)
        return stmt

    async def get_by_id(self, patient_id: str, user_role: str, user_id: str) -> Optional[Patient]:
        """
        Fetches a single patient by ID subjected to RLS.

        Args:
            patient_id: The UUID of the patient.
            user_role: Role from the JWT context.
            user_id: User UUID from the JWT context.

        Returns:
            Patient entity if found and authorized, else None.
        """
        stmt = select(Patient).where(Patient.id == patient_id)
        stmt = self._apply_rls(stmt, user_role, user_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_patients(self, limit: int, offset: int, user_role: str, user_id: str) -> List[Patient]:
        """
        Lists patients subjected to RLS with pagination.
        """
        stmt = select(Patient)
        stmt = self._apply_rls(stmt, user_role, user_id)
        stmt = stmt.limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, patient: Patient) -> Patient:
        """
        Persists a new Patient entity.
        
        Args:
            patient: The populated Patient domain entity.
            
        Returns:
            The persisted Patient entity.
        """
        self.session.add(patient)
        await self.session.commit()
        await self.session.refresh(patient)
        return patient

    async def update(self, patient: Patient) -> Patient:
        """
        Updates an existing Patient entity.
        
        Args:
            patient: The populated Patient domain entity.
            
        Returns:
            The persisted Patient entity.
        """
        self.session.add(patient)
        await self.session.commit()
        await self.session.refresh(patient)
        return patient
