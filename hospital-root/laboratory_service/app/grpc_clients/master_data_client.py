"""gRPC Client for interacting with MasterDataService."""

import asyncio
import logging
import grpc
from typing import Optional, List, Dict, Any
from generated import master_data_pb2, master_data_pb2_grpc
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

    async def get_exam_types(self, jwt_token: str) -> List[Dict[str, Any]]:
        """Fetch lab examination types."""
        max_retries = 3
        base_delay = 1.0
        
        request = master_data_pb2.EmptyRequest()
        metadata = (("authorization", f"Bearer {jwt_token}"),)

        for attempt in range(max_retries):
            try:
                response = await self.stub.GetExamTypes(request, metadata=metadata)
                return [
                    {
                        "id": et.exam_type_id,
                        "code": et.code,
                        "description": et.description,
                        "procedure_type": et.procedure_type,
                    }
                    for et in response.exam_types
                ]
            except grpc.RpcError as e:
                # UNAUTHENTICATED shouldn't be retried
                if e.code() == grpc.StatusCode.UNAUTHENTICATED:
                    logger.warning(f"MasterDataService GetExamTypes auth error: {e.details()}")
                    return []
                
                logger.error(f"Error calling MasterDataService (Attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(base_delay * (2 ** attempt))
                
        return []
