"""Data-access repository for master_data_service.

All database interactions are encapsulated here.  Read methods are designed
to be called from an in-memory cache layer; write methods record the Admin
user ID for audit purposes and must be executed within an explicit transaction.
"""

import logging
from datetime import datetime
from functools import lru_cache
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models import (
    Disease,
    DiseaseType,
    ExamType,
    OperationType,
    ProcedureTypeEnum,
    Supplier,
    Ward,
)

logger = logging.getLogger(__name__)


class EntityNotFoundError(Exception):
    """Raised when a requested reference entity cannot be located."""


class DuplicateCodeError(Exception):
    """Raised when an upsert would violate a unique code constraint."""


class MasterDataRepository:
    """
    Provides all read/write operations against the reference_db schema.
    Instances must be used within the scope of an active AsyncSession.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Ward operations
    # ------------------------------------------------------------------

    async def get_all_wards(self) -> List[Ward]:
        """Return all ward records ordered alphabetically by name."""
        result = await self._session.execute(
            select(Ward).order_by(Ward.name)
        )
        return list(result.scalars().all())

    async def get_ward_by_id(self, ward_id: str) -> Optional[Ward]:
        """Return a single Ward by primary key, or None if absent."""
        result = await self._session.execute(
            select(Ward).where(Ward.id == ward_id)
        )
        return result.scalar_one_or_none()

    async def upsert_ward(
        self,
        *,
        ward_id: Optional[str],
        code: str,
        name: str,
        beds_count: int,
        is_opd: bool,
        admin_id: str,
    ) -> Ward:
        """
        Create a new Ward when ward_id is None/empty, or update the existing one.

        Records admin_id for compliance auditing and raises EntityNotFoundError
        when an update targets a non-existent record.
        """
        if ward_id:
            ward = await self.get_ward_by_id(ward_id)
            if ward is None:
                raise EntityNotFoundError(f"Ward '{ward_id}' not found.")
            ward.code       = code
            ward.name       = name
            ward.beds_count = beds_count
            ward.is_opd     = is_opd
            ward.created_by = admin_id
            ward.updated_at = datetime.utcnow()
        else:
            ward = Ward(
                code=code,
                name=name,
                beds_count=beds_count,
                is_opd=is_opd,
                created_by=admin_id,
            )
            self._session.add(ward)

        await self._session.flush()
        return ward

    # ------------------------------------------------------------------
    # Disease operations
    # ------------------------------------------------------------------

    async def get_all_diseases(self, search_term: str = "") -> List[Disease]:
        """
        Return all Disease records, optionally filtered by a case-insensitive
        search against the code or description columns.
        """
        stmt = select(Disease).options(selectinload(Disease.disease_type_rel))
        if search_term:
            pattern = f"%{search_term.lower()}%"
            stmt = stmt.where(
                Disease.code.ilike(pattern) | Disease.description.ilike(pattern)
            )
        result = await self._session.execute(stmt.order_by(Disease.code))
        return list(result.scalars().all())

    async def get_disease_by_id(self, disease_id: str) -> Optional[Disease]:
        """Return a single Disease by primary key with its type eagerly loaded."""
        result = await self._session.execute(
            select(Disease)
            .options(selectinload(Disease.disease_type_rel))
            .where(Disease.id == disease_id)
        )
        return result.scalar_one_or_none()

    async def upsert_disease(
        self,
        *,
        disease_id: Optional[str],
        code: str,
        description: str,
        disease_type_code: str,
        admin_id: str,
    ) -> Disease:
        """
        Create or update a Disease record.  Resolves disease_type_code to its
        primary key.  Raises EntityNotFoundError when the type code is unknown.
        """
        # Resolve DiseaseType by code
        dt_result = await self._session.execute(
            select(DiseaseType).where(DiseaseType.code == disease_type_code)
        )
        disease_type = dt_result.scalar_one_or_none()
        if disease_type is None:
            raise EntityNotFoundError(
                f"DiseaseType with code '{disease_type_code}' not found."
            )

        if disease_id:
            disease = await self.get_disease_by_id(disease_id)
            if disease is None:
                raise EntityNotFoundError(f"Disease '{disease_id}' not found.")
            disease.code            = code
            disease.description     = description
            disease.disease_type_id = disease_type.id
            disease.created_by      = admin_id
            disease.updated_at      = datetime.utcnow()
        else:
            disease = Disease(
                code=code,
                description=description,
                disease_type_id=disease_type.id,
                created_by=admin_id,
            )
            self._session.add(disease)

        await self._session.flush()
        return disease

    # ------------------------------------------------------------------
    # Read-only catalogue operations
    # ------------------------------------------------------------------

    async def get_all_exam_types(self) -> List[ExamType]:
        """Return all ExamType records ordered by code."""
        result = await self._session.execute(
            select(ExamType).order_by(ExamType.code)
        )
        return list(result.scalars().all())

    async def get_all_operation_types(self) -> List[OperationType]:
        """Return all OperationType records ordered by code."""
        result = await self._session.execute(
            select(OperationType).order_by(OperationType.code)
        )
        return list(result.scalars().all())

    async def get_all_suppliers(self) -> List[Supplier]:
        """Return all Supplier records ordered by name."""
        result = await self._session.execute(
            select(Supplier).order_by(Supplier.name)
        )
        return list(result.scalars().all())
