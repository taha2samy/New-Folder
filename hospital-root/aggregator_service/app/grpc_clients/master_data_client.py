"""gRPC client for the Master Data microservice.

Employs graceful degradation (returning None or empty lists on RPC failure)
to prevent reference data outages from completely bringing down the
frontend dashboard.
"""

import logging
from typing import Any, Dict, List, Optional

import grpc

from app.generated import master_data_pb2, master_data_pb2_grpc
from app.core.security import generate_jwt_token

logger = logging.getLogger(__name__)


class MasterDataClient:
    """Async client wrapping the MasterDataService gRPC stubs."""

    def __init__(self, channel: grpc.aio.Channel) -> None:
        self.stub = master_data_pb2_grpc.MasterDataServiceStub(channel)

    def _get_metadata(self, user_id: str) -> tuple[tuple[str, str]]:
        """Generate a short-lived internal JWT and package it as gRPC metadata."""
        token = generate_jwt_token(user_id=user_id, role="internal_service", expiration_minutes=5)
        return (("authorization", f"Bearer {token}"),)

    async def get_wards(self, user_id: str) -> List[Dict[str, Any]]:
        """Fetch all wards."""
        try:
            req = master_data_pb2.EmptyRequest()
            res = await self.stub.GetWards(req, metadata=self._get_metadata(user_id))
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

    async def get_diseases(self, user_id: str, search_term: str = "") -> List[Dict[str, Any]]:
        """Fetch matching diseases."""
        try:
            req = master_data_pb2.DiseaseQuery(search_term=search_term)
            res = await self.stub.GetDiseases(req, metadata=self._get_metadata(user_id))
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

    async def get_exam_types(self, user_id: str) -> List[Dict[str, Any]]:
        """Fetch lab examination types."""
        try:
            req = master_data_pb2.EmptyRequest()
            res = await self.stub.GetExamTypes(req, metadata=self._get_metadata(user_id))
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

    async def get_operation_types(self, user_id: str) -> List[Dict[str, Any]]:
        """Fetch surgical operation types."""
        try:
            req = master_data_pb2.EmptyRequest()
            res = await self.stub.GetOperationTypes(req, metadata=self._get_metadata(user_id))
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
