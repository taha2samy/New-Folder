"""gRPC client for the Master Data microservice.

Employs graceful degradation (returning None or empty lists on RPC failure)
to prevent reference data outages from completely bringing down the
frontend dashboard.
"""

import logging
from typing import Any, Dict, List, Optional

import grpc

from app.generated import master_data_pb2, master_data_pb2_grpc

logger = logging.getLogger(__name__)


class MasterDataClient:
    """Async client wrapping the MasterDataService gRPC stubs."""

    def __init__(self, channel: grpc.aio.Channel) -> None:
        self.stub = master_data_pb2_grpc.MasterDataServiceStub(channel)

    async def get_wards(self, metadata: tuple) -> List[Dict[str, Any]]:
        """Fetch all wards."""
        try:
            req = master_data_pb2.EmptyRequest()
            res = await self.stub.GetWards(req, metadata=metadata)
            return [
                {
                    "id": w.ward_id,
                    "code": w.code,
                    "name": w.name,
                    "beds_count": w.beds_count,
                    "is_opd": w.is_opd,
                }
                for w in res.wards
            ]
        except grpc.RpcError as e:
            logger.error("MasterDataService.GetWards failed: %s", e.details())
            return []

    async def get_diseases(self, metadata: tuple, search_term: str = "") -> List[Dict[str, Any]]:
        """Fetch matching diseases."""
        try:
            req = master_data_pb2.DiseaseQuery(search_term=search_term)
            res = await self.stub.GetDiseases(req, metadata=metadata)
            return [
                {
                    "id": d.disease_id,
                    "code": d.code,
                    "description": d.description,
                    "disease_type": d.disease_type,
                }
                for d in res.diseases
            ]
        except grpc.RpcError as e:
            logger.error("MasterDataService.GetDiseases failed: %s", e.details())
            return []

    async def get_exam_types(self, metadata: tuple) -> List[Dict[str, Any]]:
        """Fetch lab examination types."""
        try:
            req = master_data_pb2.EmptyRequest()
            res = await self.stub.GetExamTypes(req, metadata=metadata)
            return [
                {
                    "id": et.exam_type_id,
                    "code": et.code,
                    "description": et.description,
                    "procedure_type": et.procedure_type,
                }
                for et in res.exam_types
            ]
        except grpc.RpcError as e:
            logger.error("MasterDataService.GetExamTypes failed: %s", e.details())
            return []

    async def get_operation_types(self, metadata: tuple) -> List[Dict[str, Any]]:
        """Fetch surgical operation types."""
        try:
            req = master_data_pb2.EmptyRequest()
            res = await self.stub.GetOperationTypes(req, metadata=metadata)
            return [
                {
                    "id": ot.operation_type_id,
                    "code": ot.code,
                    "description": ot.description,
                    "is_major": ot.is_major,
                }
                for ot in res.operation_types
            ]
        except grpc.RpcError as e:
            logger.error("MasterDataService.GetOperationTypes failed: %s", e.details())
            return []

    async def get_beds(self, metadata: tuple, ward_id: str) -> List[Dict[str, Any]]:
        """Fetch beds for a ward."""
        try:
            req = master_data_pb2.WardQuery(ward_id=ward_id)
            res = await self.stub.GetBedsByWard(req, metadata=metadata)
            return [
                {
                    "id": b.bed_id,
                    "code": b.bed_code,
                    "ward_id": b.ward_id,
                    "status": b.status,
                    "category": b.category,
                }
                for b in res.beds
            ]
        except grpc.RpcError as e:
            logger.error("MasterDataService.GetBedsByWard failed: %s", e.details())
            return []

    async def get_all_beds(self, metadata: tuple) -> List[Dict[str, Any]]:
        """Fetch all non-deleted beds in the hospital (Optimized for Bulk)."""
        try:
            req = master_data_pb2.EmptyRequest()
            res = await self.stub.GetAllBeds(req, metadata=metadata)
            return [
                {
                    "id": b.bed_id,
                    "code": b.bed_code,
                    "ward_id": b.ward_id,
                    "status": b.status,
                    "category": b.category,
                }
                for b in res.beds
            ]
        except grpc.RpcError as e:
            logger.error("MasterDataService.GetAllBeds failed: %s", e.details())
            return []

    async def mark_bed_as_ready(self, bed_id: str, metadata: tuple) -> Optional[Dict[str, Any]]:
        """Transitions a bed from CLEANING to AVAILABLE via gRPC."""
        try:
            req = master_data_pb2.BedQuery(bed_id=bed_id)
            res = await self.stub.MarkBedAsReady(req, metadata=metadata)
            return {
                "id": res.bed_id,
                "code": res.bed_code,
                "ward_id": res.ward_id,
                "status": res.status,
                "category": res.category
            }
        except grpc.RpcError as e:
            logger.error("MasterDataService.MarkBedAsReady failed: %s", e.details())
            return None

    async def upsert_exam_type(
        self,
        code: str,
        description: str,
        procedure_type: int,
        metadata: tuple,
        exam_type_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Create or update an ExamType."""
        try:
            req = master_data_pb2.UpsertExamTypeRequest(
                exam_type_id=exam_type_id or "",
                code=code,
                description=description,
                procedure_type=procedure_type,
            )
            res = await self.stub.UpsertExamType(req, metadata=metadata)
            return {
                "id": res.exam_type_id,
                "code": res.code,
                "description": res.description,
                "procedure_type": res.procedure_type,
            }
        except grpc.RpcError as e:
            logger.error("MasterDataService.UpsertExamType failed: %s", e.details())
            return None

    async def upsert_operation_type(
        self,
        code: str,
        description: str,
        is_major: bool,
        metadata: tuple,
        operation_type_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Create or update an OperationType."""
        try:
            req = master_data_pb2.UpsertOperationTypeRequest(
                operation_type_id=operation_type_id or "",
                code=code,
                description=description,
                is_major=is_major,
            )
            res = await self.stub.UpsertOperationType(req, metadata=metadata)
            return {
                "id": res.operation_type_id,
                "code": res.code,
                "description": res.description,
                "is_major": res.is_major,
            }
        except grpc.RpcError as e:
            logger.error("MasterDataService.UpsertOperationType failed: %s", e.details())
            return None
