"""gRPC async wrapper for ClinicalEncounterService."""

import grpc
import logging
from typing import List
from generated import clinical_pb2, clinical_pb2_grpc

logger = logging.getLogger(__name__)

class ClinicalClient:
    def __init__(self, channel: grpc.aio.Channel):
        self.stub = clinical_pb2_grpc.ClinicalEncounterServiceStub(channel)

    async def get_encounters(self, patient_id: str, metadata: tuple) -> List[dict]:
        encounters = []
        try:
            request = clinical_pb2.PatientEncountersRequest(patient_id=patient_id)
            async for response in self.stub.GetPatientEncounters(request, metadata=metadata):
                encounters.append({
                    "encounter_id": response.encounter_id,
                    "status": response.status,
                    "encounter_type": response.encounter_type,
                    "diagnosis_codes": list(response.diagnosis_codes)
                })
        except grpc.RpcError as e:
            logger.error(f"gRPC PatientEncountersRequest failed: {e}")
        return encounters
