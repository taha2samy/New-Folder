"""gRPC Client for interacting with PatientService."""

import asyncio
import logging
import grpc
from typing import Optional
from generated import patient_pb2, patient_pb2_grpc
from app.core.config import settings

logger = logging.getLogger(__name__)

class PatientServiceClient:
    """
    gRPC Client wrapper to query the PatientService natively.
    Includes Exponential Backoff retries.
    """
    def __init__(self):
        self.channel = grpc.aio.insecure_channel(settings.PATIENT_SERVICE_ADDR)
        self.stub = patient_pb2_grpc.PatientServiceStub(self.channel)

    async def get_patient_by_id(self, patient_id: str, jwt_token: str) -> Optional[dict]:
        """
        Retrieves a patient by id. Uses exponential backoff on connection errors.
        """
        max_retries = 3
        base_delay = 1.0
        
        request = patient_pb2.PatientRequest(id=patient_id)
        metadata = (("authorization", f"Bearer {jwt_token}"),)

        for attempt in range(max_retries):
            try:
                response = await self.stub.GetPatientById(request, metadata=metadata)
                return {
                    "id": response.id,
                    "code": response.code,
                    "is_deleted": response.is_deleted,
                    "status": "active" if not response.is_deleted else "deleted"
                }
            except grpc.RpcError as e:
                # UNAUTHENTICATED or NOT_FOUND shouldn't be retried
                if e.code() in [grpc.StatusCode.UNAUTHENTICATED, grpc.StatusCode.NOT_FOUND]:
                    logger.warning(f"Patient {patient_id} not retrievable: {e.details()}")
                    return None
                
                logger.error(f"Error calling patient_service (Attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(base_delay * (2 ** attempt))
                
        return None
