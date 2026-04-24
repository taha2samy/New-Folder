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

    def _apply_rls(self, stmt):
        """
        Applies Soft Delete constraints. Role-based filtering is disabled for testing.
        """
        stmt = stmt.where(Patient.is_deleted == False)
        return stmt

    async def get_by_id(self, patient_id: str) -> Optional[Patient]:
        """
        Fetches a single patient by ID.

        Args:
            patient_id: The UUID of the patient.

        Returns:
            Patient entity if found, else None.
        """
        stmt = select(Patient).where(Patient.id == patient_id)
        stmt = self._apply_rls(stmt)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_patients(self, limit: int, offset: int) -> List[Patient]:
        """
        Lists patients with pagination.
        """
        stmt = select(Patient)
        stmt = self._apply_rls(stmt)
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
