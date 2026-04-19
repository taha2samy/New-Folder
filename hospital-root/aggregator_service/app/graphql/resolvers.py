"""GraphQL Resolvers and parallel orchestration."""

import asyncio
import time
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
    ReferenceDataSummary,
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

_MASTER_DATA_CACHE = {
    "timestamp": 0,
    "wards": {},
    "diseases": {},
    "exams": {},
}

async def _get_cached_master_data(master_client: MasterDataClient, token: str):
    """Refreshes master data if TTL (5 mins) expired."""
    current_time = time.time()
    if current_time - _MASTER_DATA_CACHE["timestamp"] > 300:
        wards_fut = master_client.get_wards(token)
        diseases_fut = master_client.get_diseases(token)
        exams_fut = master_client.get_exam_types(token)
        
        wards_data, diseases_data, exams_data = await asyncio.gather(
            wards_fut, diseases_fut, exams_fut, return_exceptions=True
        )
        
        if not isinstance(wards_data, Exception):
            _MASTER_DATA_CACHE["wards"] = {w["id"]: w["name"] for w in wards_data}
        if not isinstance(diseases_data, Exception):
            _MASTER_DATA_CACHE["diseases"] = {d["id"]: d["description"] for d in diseases_data}
        if not isinstance(exams_data, Exception):
            _MASTER_DATA_CACHE["exams"] = {e["id"]: e["description"] for e in exams_data}
            
        _MASTER_DATA_CACHE["timestamp"] = current_time

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

        # Fetch master data cache
        # Note: In a real system, you'd extract the pure string JWT token out of `metadata`
        # Because `metadata` is a tuple like (("authorization", "Bearer xyz"),)
        token = ""
        for k, v in metadata:
            if k.lower() == "authorization":
                token = v.replace("Bearer ", "")
                break
        if not token:
            for k, v in metadata:
                if k.lower() == "x-jwt-token":
                    token = v
                    break
        
        master_data_client: MasterDataClient = client_refs["master_data"]
        await _get_cached_master_data(master_data_client, token)

        # Build partial representations cleanly so a single service failure
        # does not bring down the entire unified graph response.
        encounters_list = None
        if encounters_data is not None and not isinstance(encounters_data, Exception):
            encounters_list = []
            for enc in encounters_data:
                ward_id = enc.get("ward")
                ward_name = _MASTER_DATA_CACHE["wards"].get(ward_id) if ward_id else None
                diag_codes = enc.get("diagnosis_codes", [])
                diag_names = [_MASTER_DATA_CACHE["diseases"].get(code, code) for code in diag_codes]
                
                encounters_list.append(EncounterType(
                    encounter_id=enc["encounter_id"],
                    status=enc["status"],
                    encounter_type=enc["encounter_type"],
                    diagnosis_codes=diag_codes,
                    ward_id=ward_id,
                    ward_name=ward_name,
                    diagnoses_names=diag_names
                ))

        medications_list = None
        if medications_data is not None and not isinstance(medications_data, Exception):
            medications_list = [MedicationType(**med) for med in medications_data]

        lab_results_list = None
        if lab_data is not None and not isinstance(lab_data, Exception):
            lab_results_list = []
            for lr in lab_data:
                exam_type_id = lr.get("test_name")
                mapped_name = _MASTER_DATA_CACHE["exams"].get(exam_type_id, exam_type_id)
                lab_results_list.append(LabResultType(
                    id=lr["id"],
                    test_name=mapped_name,
                    status=lr["status"],
                    date=lr["date"],
                    result_value=lr.get("result_value"),
                    result_description=lr.get("result_description")
                ))

        return PatientSummary(
            patient=PatientType(**patient_data),
            encounters=encounters_list,
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
