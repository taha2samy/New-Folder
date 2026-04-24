"""gRPC async wrapper for PatientService."""

import grpc
import logging
from typing import Optional
from app.generated import patient_pb2, patient_pb2_grpc

logger = logging.getLogger(__name__)

class PatientClient:
    def __init__(self, channel: grpc.aio.Channel):
        self.stub = patient_pb2_grpc.PatientServiceStub(channel)

    async def get_patient(self, patient_id: str, metadata: tuple) -> Optional[dict]:
        try:
            request = patient_pb2.PatientRequest(id=patient_id)
            response = await self.stub.GetPatientById(request, metadata=metadata)
            return {
                "id": response.id,
                "code": response.code,
                "full_name": response.full_name,
                "birth_date": response.birth_date,
                "sex": patient_pb2.Sex.Name(response.sex),
                "blood_type": response.blood_type,
                "is_insured": response.is_insured
            }
        except grpc.RpcError as e:
            logger.error(f"gRPC PatientRequest failed: {e}")
            return None
