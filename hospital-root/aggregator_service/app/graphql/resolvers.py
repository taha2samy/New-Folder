"""GraphQL Resolvers and parallel orchestration."""

import strawberry
import asyncio
from typing import Optional
from strawberry.types import Info
from app.graphql.schema import PatientType, PatientSummary, EncounterType
from app.grpc_clients.patient_client import PatientClient
from app.grpc_clients.clinical_client import ClinicalClient

_patient_client: Optional[PatientClient] = None
_clinical_client: Optional[ClinicalClient] = None

def init_clients(patient_client: PatientClient, clinical_client: ClinicalClient):
    global _patient_client, _clinical_client
    _patient_client = patient_client
    _clinical_client = clinical_client

@strawberry.type
class Query:
    @strawberry.field
    async def patient_by_id(self, info: Info, id: strawberry.ID) -> Optional[PatientType]:
        context = info.context
        metadata = context.metadata
        
        patient_data = await _patient_client.get_patient(str(id), metadata)
        if not patient_data:
            return None
            
        return PatientType(**patient_data)

    @strawberry.field
    async def patient_full_dashboard(self, info: Info, id: strawberry.ID) -> Optional[PatientSummary]:
        context = info.context
        metadata = context.metadata

        # Parallelize independent gRPC downstream calls
        patient_task = asyncio.create_task(_patient_client.get_patient(str(id), metadata))
        encounters_task = asyncio.create_task(_clinical_client.get_encounters(str(id), metadata))

        patient_data, encounters_data = await asyncio.gather(patient_task, encounters_task)

        if not patient_data:
            # If main patient fails, dashboard fails entirely for this patient id
            return None

        # Build partial representations cleanly if encounters fail.
        encounters_list = None
        if encounters_data is not None:
            encounters_list = [EncounterType(**enc) for enc in encounters_data]

        return PatientSummary(
            patient=PatientType(**patient_data),
            encounters=encounters_list
        )
