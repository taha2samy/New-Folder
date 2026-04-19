"""Data-access repository for laboratory_service.

All database interactions are encapsulated here to keep the gRPC handler free
of SQLAlchemy specifics and to facilitate unit testing via dependency injection.
"""

import logging
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models import LabRequest, LabResult, TestStatus

logger = logging.getLogger(__name__)


class LabRequestNotFoundError(Exception):
    """Raised when a LabRequest lookup fails."""


class DuplicateResultError(Exception):
    """Raised when a result submission targets a request that already has a result."""


class LaboratoryRepository:
    """
    Provides all read/write operations against the laboratory schema.
    Instances must be used within the scope of an active AsyncSession.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # LabRequest operations
    # ------------------------------------------------------------------

    async def create_lab_request(
        self,
        patient_id: str,
        exam_type_id: str,
        material: str,
        admission_id: Optional[str] = None,
    ) -> LabRequest:
        """
        Persist a new LabRequest in PENDING status and return the managed object.
        The caller is responsible for committing the enclosing transaction.
        """
        lab_request = LabRequest(
            patient_id=patient_id,
            exam_type_id=exam_type_id,
            material=material,
            admission_id=admission_id or None,
            status=TestStatus.PENDING,
        )
        self._session.add(lab_request)
        await self._session.flush()   # Populate PK without committing
        return lab_request

    async def get_lab_request_by_id(self, request_id: str) -> Optional[LabRequest]:
        """
        Retrieve a single non-deleted LabRequest by its primary key.
        Eagerly loads the associated LabResult to avoid N+1 queries.
        """
        stmt = (
            select(LabRequest)
            .options(selectinload(LabRequest.result))
            .where(LabRequest.id == request_id, LabRequest.is_deleted == False)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_patient_lab_history(self, patient_id: str) -> List[LabRequest]:
        """
        Retrieve all non-deleted LabRequest records for a patient, each eagerly
        joined with its LabResult (when present), ordered by request date descending.
        """
        stmt = (
            select(LabRequest)
            .options(selectinload(LabRequest.result))
            .where(
                LabRequest.patient_id == patient_id,
                LabRequest.is_deleted == False,
            )
            .order_by(LabRequest.request_date.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # LabResult operations
    # ------------------------------------------------------------------

    async def create_lab_result(
        self,
        request_id: str,
        description: str,
        value: str,
        technician_id: str,
    ) -> LabResult:
        """
        Attach a result to an existing LabRequest and advance its status to
        COMPLETED.  Raises LabRequestNotFoundError or DuplicateResultError on
        pre-condition failures.  The caller owns the transaction.
        """
        lab_request = await self.get_lab_request_by_id(request_id)
        if lab_request is None:
            raise LabRequestNotFoundError(
                f"LabRequest '{request_id}' does not exist or has been deleted."
            )

        if lab_request.result is not None:
            raise DuplicateResultError(
                f"LabRequest '{request_id}' already has a submitted result."
            )

        lab_result = LabResult(
            request_id=request_id,
            description=description,
            value=value,
            technician_id=technician_id,
        )
        lab_request.status = TestStatus.COMPLETED

        self._session.add(lab_result)
        await self._session.flush()
        return lab_result
