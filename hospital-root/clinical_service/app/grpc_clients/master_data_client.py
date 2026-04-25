"""gRPC Client for interacting with MasterDataService."""

import asyncio
import logging
import grpc
from typing import Optional, List, Dict, Any
from app.generated import master_data_pb2, master_data_pb2_grpc
from app.core.config import settings

logger = logging.getLogger(__name__)

class MasterDataClient:
    """
    gRPC Client wrapper to query the MasterDataService natively.
    Includes Exponential Backoff retries.
    """
    def __init__(self):
        self.channel = grpc.aio.insecure_channel(settings.MASTER_DATA_SERVICE_ADDR)
        self.stub = master_data_pb2_grpc.MasterDataServiceStub(self.channel)

    async def get_wards(self, jwt_token: str) -> List[Dict[str, Any]]:
        """Retrieves wards."""
        max_retries = 3
        base_delay = 1.0
        
        request = master_data_pb2.EmptyRequest()
        metadata = (("authorization", f"Bearer {jwt_token}"),)

        for attempt in range(max_retries):
            try:
                response = await self.stub.GetWards(request, metadata=metadata)
                return [{"id": w.ward_id, "name": w.name} for w in response.wards]
            except grpc.RpcError as e:
                # UNAUTHENTICATED shouldn't be retried
                if e.code() == grpc.StatusCode.UNAUTHENTICATED:
                    logger.warning(f"MasterDataService GetWards auth error: {e.details()}")
                    return []
                
                logger.error(f"Error calling MasterDataService (Attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(base_delay * (2 ** attempt))
                
        return []

    async def get_diseases(self, jwt_token: str) -> List[Dict[str, Any]]:
        """Retrieves diseases."""
        max_retries = 3
        base_delay = 1.0
        
        request = master_data_pb2.DiseaseQuery(search_term="")
        metadata = (("authorization", f"Bearer {jwt_token}"),)

        for attempt in range(max_retries):
            try:
                response = await self.stub.GetDiseases(request, metadata=metadata)
                return [{"id": d.disease_id, "code": d.code} for d in response.diseases]
            except grpc.RpcError as e:
                if e.code() == grpc.StatusCode.UNAUTHENTICATED:
                    logger.warning(f"MasterDataService GetDiseases auth error: {e.details()}")
                    return []
                
                logger.error(f"Error calling MasterDataService (Attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(base_delay * (2 ** attempt))
                
        return []

    async def get_beds_by_ward(self, ward_id: str, jwt_token: str) -> List[Dict[str, Any]]:
        """Retrieves beds for a ward."""
        request = master_data_pb2.WardQuery(ward_id=ward_id)
        metadata = (("authorization", f"Bearer {jwt_token}"),)
        try:
            response = await self.stub.GetBedsByWard(request, metadata=metadata)
            return [
                {
                    "id": b.bed_id,
                    "code": b.bed_code,
                    "status": b.status,
                    "category": b.category
                } for b in response.beds
            ]
        except grpc.RpcError as e:
            logger.error(f"Error calling MasterDataService GetBedsByWard: {e}")
            return []

    async def update_bed_status(self, bed_id: str, status: int, jwt_token: str) -> bool:
        """Updates bed status (idempotent)."""
        request = master_data_pb2.UpdateBedStatusRequest(bed_id=bed_id, status=status)
        metadata = (("authorization", f"Bearer {jwt_token}"),)
        try:
            await self.stub.UpdateBedStatus(request, metadata=metadata)
            return True
        except grpc.RpcError as e:
            logger.error(f"Error calling MasterDataService UpdateBedStatus: {e}")
            return False
