"""gRPC Client for interacting with MasterDataService from Billing service."""

import logging
import grpc
from typing import Optional, Dict, Any
from app.generated import master_data_pb2, master_data_pb2_grpc
from app.core.config import settings

from app.core.security import generate_internal_token

logger = logging.getLogger(__name__)

class MasterDataClient:
    def __init__(self):
        self.channel = grpc.aio.insecure_channel(settings.MASTER_DATA_SERVICE_ADDR)
        self.stub = master_data_pb2_grpc.MasterDataServiceStub(self.channel)

    async def get_bed(self, bed_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves bed details for category mapping, using internal auth."""
        request = master_data_pb2.BedQuery(bed_id=bed_id)
        token = generate_internal_token()
        metadata = (("authorization", f"Bearer {token}"),)
        try:
            response = await self.stub.GetBed(request, metadata=metadata)
            return {
                "id": response.bed_id,
                "code": response.bed_code,
                "ward_id": response.ward_id,
                "status": response.status,
                "category": response.category
            }
        except grpc.RpcError as e:
            logger.error(f"Error calling MasterDataService GetBed: {e}")
            return None
