"""gRPC Client for interacting with ClinicalService from Billing service."""

import logging
import grpc
from typing import List, Dict, Any
from app.generated import clinical_pb2, clinical_pb2_grpc
from app.core.config import settings

logger = logging.getLogger(__name__)

class ClinicalClient:
    def __init__(self):
        self.channel = grpc.aio.insecure_channel(settings.CLINICAL_SERVICE_ADDR)
        self.stub = clinical_pb2_grpc.ClinicalEncounterServiceStub(self.channel)

    async def get_active_admissions(self) -> List[Dict[str, Any]]:
        """Retrieves all active admissions for recurring billing."""
        request = clinical_pb2.EmptyRequest()
        admissions = []
        try:
            async for response in self.stub.GetActiveAdmissions(request):
                admissions.append({
                    "encounter_id": response.encounter_id,
                    "patient_id": response.patient_id,
                    "bed_id": response.bed_id,
                    "ward_id": response.ward_id,
                    "created_at": response.created_at
                })
            return admissions
        except grpc.RpcError as e:
            logger.error(f"Error calling ClinicalService GetActiveAdmissions: {e}")
            return []
