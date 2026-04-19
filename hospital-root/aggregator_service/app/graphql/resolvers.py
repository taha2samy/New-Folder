"""GraphQL Resolvers and parallel orchestration."""

import asyncio
from typing import Optional

import strawberry
from strawberry.types import Info

from app.graphql.schema import (
    DispenseResponse,
    EncounterType,
    LabResultType,
    MedicationType,
    PatientSummary,
    PatientType,
    ReferenceDataSummary,
    ClinicalEncounterType,
    WardType,
    DiseaseRefType,
    ExamTypeRef,
    OperationTypeRef,
)
from app.grpc_clients.clinical_client import ClinicalClient
from app.grpc_clients.laboratory_client import LaboratoryClient
from app.grpc_clients.patient_client import PatientClient
from app.grpc_clients.pharmacy_client import PharmacyClient
from app.grpc_clients.master_data_client import MasterDataClient

client_refs = {
    "patient": None,
    "clinical": None,
    "pharmacy": None,
    "laboratory": None,
    "master_data": None,
}

def init_clients(
    patient_client: PatientClient,
    clinical_client: ClinicalClient,
    pharmacy_client: PharmacyClient,
    laboratory_client: LaboratoryClient,
    master_data_client: MasterDataClient,
) -> None:
    client_refs["patient"] = patient_client
    client_refs["clinical"] = clinical_client
    client_refs["pharmacy"] = pharmacy_client
    client_refs["laboratory"] = laboratory_client
    client_refs["master_data"] = master_data_client

@strawberry.type
class Query:
    @strawberry.field
    async def patient_by_id(self, info: Info, id: strawberry.ID) -> Optional[PatientType]:
        context = info.context
        metadata = context.metadata
        
        patient_client: PatientClient = client_refs["patient"]
        patient_data = await patient_client.get_patient(str(id), metadata)
        if not patient_data:
            return None
            
        return PatientType(**patient_data)

    @strawberry.field
    async def patient_full_dashboard(self, info: Info, id: strawberry.ID) -> Optional[PatientSummary]:
        context = info.context
        metadata = context.metadata

        # Parallelise all independent downstream gRPC calls.
        patient_client: PatientClient = client_refs["patient"]
        clinical_client: ClinicalClient = client_refs["clinical"]
        pharmacy_client: PharmacyClient = client_refs["pharmacy"]
        laboratory_client: LaboratoryClient = client_refs["laboratory"]

        patient_task     = asyncio.create_task(patient_client.get_patient(str(id), metadata))
        encounters_task  = asyncio.create_task(clinical_client.get_encounters(str(id), metadata))
        medications_task = asyncio.create_task(pharmacy_client.get_patient_medications(str(id), metadata))
        lab_task         = asyncio.create_task(laboratory_client.get_patient_lab_history(str(id), metadata))

        patient_data, encounters_data, medications_data, lab_data = await asyncio.gather(
            patient_task, encounters_task, medications_task, lab_task,
            return_exceptions=True,
        )

        if isinstance(patient_data, Exception) or not patient_data:
            # Core patient data is mandatory; abort the entire dashboard on failure.
            return None

        # Build partial representations cleanly so a single service failure
        # does not bring down the entire unified graph response.
        encounters_list = None
        if encounters_data is not None and not isinstance(encounters_data, Exception):
            encounters_list = [ClinicalEncounterType(**enc) for enc in encounters_data]

        medications_list = None
        if medications_data is not None and not isinstance(medications_data, Exception):
            medications_list = [MedicationType(**med) for med in medications_data]

        lab_results_list = None
        if lab_data is not None and not isinstance(lab_data, Exception):
            lab_results_list = [LabResultType(**lr) for lr in lab_data]

        return PatientSummary(
            patient=PatientType(**patient_data),
            recent_encounters=encounters_list,
            medications=medications_list,
            lab_results=lab_results_list,
        )

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def dispense_medicine(self, info: Info, pharmaceutical_id: str, quantity: int, patient_id: str) -> DispenseResponse:
        context = info.context
        metadata = context.metadata
        
        pharmacy_client: PharmacyClient = client_refs["pharmacy"]
        result = await pharmacy_client.dispense_medicine(pharmaceutical_id, quantity, patient_id, metadata)
        return DispenseResponse(**result)
