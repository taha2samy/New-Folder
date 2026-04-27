"""Data-access repository for master_data_service.

All database interactions are encapsulated here.  Read methods are designed
to be called from an in-memory cache layer; write methods record the Admin
user ID for audit purposes and must be executed within an explicit transaction.
"""

import logging
from datetime import datetime
from functools import lru_cache
from typing import List, Optional

from sqlalchemy import select, func
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
    Bed,
    BedStatusEnum,
    BedCategory,
)

logger = logging.getLogger(__name__)


class EntityNotFoundError(Exception):
    """Raised when a requested reference entity cannot be located."""


class DuplicateCodeError(Exception):
    """Raised when an upsert would violate a unique code constraint."""


class MasterDataRepository:
    """
    Provides all read/write operations against the master_data_db schema.
    Instances must be used within the scope of an active AsyncSession.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Ward operations
    # ------------------------------------------------------------------

    async def get_all_wards(self) -> List[Ward]:
        """
        Return all ward records ordered alphabetically by name.
        The beds_count is dynamically calculated from active beds.
        """
        # Subquery to count active (non-deleted) beds per ward
        bed_count_sub = (
            select(Bed.ward_id, func.count(Bed.id).label("active_beds"))
            .where(Bed.is_deleted == False)
            .group_by(Bed.ward_id)
            .subquery()
        )

        result = await self._session.execute(
            select(Ward, bed_count_sub.c.active_beds)
            .outerjoin(bed_count_sub, Ward.id == bed_count_sub.c.ward_id)
            .order_by(Ward.name)
        )
        
        wards = []
        for ward, active_beds in result.all():
            ward.beds_count = active_beds or 0
            wards.append(ward)
        return wards

    async def get_ward_by_id(self, ward_id: str) -> Optional[Ward]:
        """Return a single Ward by primary key, or None if absent."""
        bed_count_sub = (
            select(func.count(Bed.id).label("active_beds"))
            .where((Bed.ward_id == ward_id) & (Bed.is_deleted == False))
            .scalar_subquery()
        )

        result = await self._session.execute(
            select(Ward, bed_count_sub).where(Ward.id == ward_id)
        )
        row = result.one_or_none()
        if not row:
            return None
        
        ward, active_beds = row
        ward.beds_count = active_beds or 0
        return ward

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
        Create or update a Ward and reconcile its Bed records.
        """
        if ward_id:
            ward = await self.get_ward_by_id(ward_id)
            if ward is None:
                raise EntityNotFoundError(f"Ward '{ward_id}' not found.")
            ward.code       = code
            ward.name       = name
            # Note: beds_count as a static field is legacy; we reconcile the Bed table records instead.
            # But we keep it in sync for documentation/Legacy UI.
            ward.is_opd     = is_opd
            ward.created_by = admin_id
            ward.updated_at = datetime.utcnow()
        else:
            ward = Ward(
                code=code,
                name=name,
                beds_count=0, # Computed reality replaces this
                is_opd=is_opd,
                created_by=admin_id,
            )
            self._session.add(ward)
            await self._session.flush() # Get ward.id

        # Beds are now managed individually via upsert_bed.
        # We compute the actual bed count rather than trusting the payload.
        ward.beds_count = await self.sync_ward_bed_count(ward.id)
        await self._session.flush()
        return ward

    async def get_beds_by_ward(self, ward_id: str) -> List[Bed]:
        """Return all non-deleted beds in a ward."""
        result = await self._session.execute(
            select(Bed)
            .options(selectinload(Bed.category_rel))
            .where((Bed.ward_id == ward_id) & (Bed.is_deleted == False))
            .order_by(Bed.code)
        )
        return list(result.scalars().all())

    async def get_all_beds(self) -> List[Bed]:
        """Return all registered, non-deleted beds in the hospital."""
        result = await self._session.execute(
            select(Bed)
            .options(selectinload(Bed.category_rel))
            .where(Bed.is_deleted == False)
            .order_by(Bed.code)
        )
        return list(result.scalars().all())

    async def get_bed_by_id(self, bed_id: str) -> Optional[Bed]:
        """Return a single non-deleted bed by ID."""
        result = await self._session.execute(
            select(Bed)
            .options(selectinload(Bed.category_rel))
            .where((Bed.id == bed_id) & (Bed.is_deleted == False))
        )
        return result.scalar_one_or_none()

    async def update_bed_status(self, bed_id: str, status: BedStatusEnum) -> Bed:
        """Update bed status with row-level locking to prevent race conditions."""
        result = await self._session.execute(
            select(Bed)
            .options(selectinload(Bed.category_rel))
            .where((Bed.id == bed_id) & (Bed.is_deleted == False))
            .with_for_update() # Row-level lock
        )
        bed = result.scalar_one_or_none()
        if not bed:
            raise EntityNotFoundError(f"Bed {bed_id} not found.")
        
        bed.status = status
        await self._session.flush()
        return bed

    async def upsert_bed(
        self,
        *,
        bed_id: Optional[str],
        code: str,
        ward_id: str,
        category_id: str,
        status: BedStatusEnum,
    ) -> Bed:
        """Create or update an individual Bed with validations."""
        # 1. Validate Ward exists
        ward_result = await self._session.execute(select(Ward).where(Ward.id == ward_id))
        if not ward_result.scalar_one_or_none():
            raise EntityNotFoundError(f"Ward '{ward_id}' not found.")

        # 2. Validate Category exists
        cat_result = await self._session.execute(select(BedCategory).where(BedCategory.id == category_id))
        if not cat_result.scalar_one_or_none():
            raise EntityNotFoundError(f"BedCategory '{category_id}' not found.")

        # 3. Check code uniqueness within ward
        code_check = await self._session.execute(
            select(Bed).where(
                (Bed.code == code) & 
                (Bed.ward_id == ward_id) & 
                (Bed.is_deleted == False) & 
                (Bed.id != (bed_id or ""))
            )
        )
        if code_check.scalar_one_or_none():
            raise DuplicateCodeError(f"Bed code '{code}' already exists in ward '{ward_id}'.")

        if bed_id:
            bed = await self.get_bed_by_id(bed_id)
            if bed is None:
                raise EntityNotFoundError(f"Bed '{bed_id}' not found.")
            bed.code = code
            bed.ward_id = ward_id
            bed.category_id = category_id
            bed.status = status
        else:
            bed = Bed(
                code=code,
                ward_id=ward_id,
                category_id=category_id,
                status=status
            )
            self._session.add(bed)

        await self._session.flush()
        
        # Reload with relationships specifically for correct gRPC translation
        return await self.get_bed_by_id(bed.id)

    async def sync_ward_bed_count(self, ward_id: str) -> int:
        """
        Calculates actual bed count and updates the Ward record.
        Ensures beds_count is dynamically validated.
        """
        ward = await self.get_ward_by_id(ward_id)
        if not ward:
            raise EntityNotFoundError(f"Ward {ward_id} not found.")
        
        count_result = await self._session.execute(
            select(func.count(Bed.id))
            .where((Bed.ward_id == ward_id) & (Bed.is_deleted == False))
        )
        actual_count = count_result.scalar() or 0
        await self._session.flush()
        return actual_count

    # ------------------------------------------------------------------
    # BedCategory operations
    # ------------------------------------------------------------------

    async def get_all_bed_categories(self) -> List[BedCategory]:
        """Return all bed category variants."""
        result = await self._session.execute(
            select(BedCategory).order_by(BedCategory.name)
        )
        return list(result.scalars().all())

    async def get_bed_category_by_id(self, cat_id: str) -> Optional[BedCategory]:
        result = await self._session.execute(
            select(BedCategory).where(BedCategory.id == cat_id)
        )
        return result.scalar_one_or_none()

    async def upsert_bed_category(
        self,
        *,
        id: Optional[str],
        name: str,
        description: str,
    ) -> BedCategory:
        if id:
            cat = await self.get_bed_category_by_id(id)
            if cat is None:
                raise EntityNotFoundError(f"BedCategory '{id}' not found.")
            cat.name = name
            cat.description = description
        else:
            cat = BedCategory(name=name, description=description)
            self._session.add(cat)
        
        await self._session.flush()
        return cat

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

    # ------------------------------------------------------------------
    # Catalogue Write operations
    # ------------------------------------------------------------------

    async def get_exam_type_by_id(self, et_id: str) -> Optional[ExamType]:
        """Return a single ExamType by primary key."""
        result = await self._session.execute(select(ExamType).where(ExamType.id == et_id))
        return result.scalar_one_or_none()

    async def get_operation_type_by_id(self, ot_id: str) -> Optional[OperationType]:
        """Return a single OperationType by primary key."""
        result = await self._session.execute(select(OperationType).where(OperationType.id == ot_id))
        return result.scalar_one_or_none()

    async def upsert_exam_type(
        self,
        *,
        exam_type_id: Optional[str],
        code: str,
        description: str,
        procedure_type: ProcedureTypeEnum,
    ) -> ExamType:
        """Create or update an ExamType record."""
        if exam_type_id:
            exam_type = await self.get_exam_type_by_id(exam_type_id)
            if exam_type is None:
                raise EntityNotFoundError(f"ExamType '{exam_type_id}' not found.")
            exam_type.code           = code
            exam_type.description    = description
            exam_type.procedure_type = procedure_type
        else:
            exam_type = ExamType(
                code=code,
                description=description,
                procedure_type=procedure_type,
            )
            self._session.add(exam_type)

        await self._session.flush()
        return exam_type

    async def upsert_operation_type(
        self,
        *,
        operation_type_id: Optional[str],
        code: str,
        description: str,
        is_major: bool,
    ) -> OperationType:
        """Create or update an OperationType record."""
        if operation_type_id:
            op_type = await self.get_operation_type_by_id(operation_type_id)
            if op_type is None:
                raise EntityNotFoundError(f"OperationType '{operation_type_id}' not found.")
            op_type.code        = code
            op_type.description = description
            op_type.is_major    = is_major
        else:
            op_type = OperationType(
                code=code,
                description=description,
                is_major=is_major,
            )
            self._session.add(op_type)

        await self._session.flush()
        return op_type
