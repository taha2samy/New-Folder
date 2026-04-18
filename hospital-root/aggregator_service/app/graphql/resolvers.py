"""GraphQL Resolvers and parallel orchestration."""

import strawberry
import asyncio
from typing import Optional
from strawberry.types import Info
from app.graphql.schema import PatientType, PatientSummary, EncounterType, MedicationType, DispenseResponse
from app.grpc_clients.patient_client import PatientClient
from app.grpc_clients.clinical_client import ClinicalClient
from app.grpc_clients.pharmacy_client import PharmacyClient

_patient_client: Optional[PatientClient] = None
_clinical_client: Optional[ClinicalClient] = None
_pharmacy_client: Optional[PharmacyClient] = None

def init_clients(patient_client: PatientClient, clinical_client: ClinicalClient, pharmacy_client: PharmacyClient):
    global _patient_client, _clinical_client, _pharmacy_client
    _patient_client = patient_client
    _clinical_client = clinical_client
    _pharmacy_client = pharmacy_client

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
        medications_task = asyncio.create_task(_pharmacy_client.get_patient_medications(str(id), metadata))

        patient_data, encounters_data, medications_data = await asyncio.gather(
            patient_task, encounters_task, medications_task, return_exceptions=True
        )

        if isinstance(patient_data, Exception) or not patient_data:
            # If main patient fails or throws, dashboard fails entirely
            return None

        # Build partial representations cleanly if other tasks fail
        encounters_list = None
        if encounters_data is not None and not isinstance(encounters_data, Exception):
            encounters_list = [EncounterType(**enc) for enc in encounters_data]

        medications_list = None
        if medications_data is not None and not isinstance(medications_data, Exception):
            medications_list = [MedicationType(**med) for med in medications_data]

        return PatientSummary(
            patient=PatientType(**patient_data),
            encounters=encounters_list,
            medications=medications_list
        )

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def dispense_medicine(self, info: Info, pharmaceutical_id: str, quantity: int, patient_id: str) -> DispenseResponse:
        context = info.context
        metadata = context.metadata
        
        # We simply await the pharmacy call
        result = await _pharmacy_client.dispense_medicine(pharmaceutical_id, quantity, patient_id, metadata)
        return DispenseResponse(**result)
