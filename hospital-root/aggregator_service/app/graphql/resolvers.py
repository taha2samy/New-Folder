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
    BillingSummaryType,
    ReferenceDataSummary,
    WardType,
    BedType,
    BedStatus,
    DiseaseRefType,
    ExamTypeRef,
    OperationTypeRef,
    BillItemType,
    MarkBedResponse,
)
from app.generated import master_data_pb2
from app.grpc_clients.clinical_client import ClinicalClient
from app.grpc_clients.laboratory_client import LaboratoryClient
from app.grpc_clients.patient_client import PatientClient
from app.grpc_clients.pharmacy_client import PharmacyClient
from app.grpc_clients.master_data_client import MasterDataClient
from app.grpc_clients.billing_client import BillingClient

_BED_STATUS_MAP = {
    master_data_pb2.BedStatus.AVAILABLE:   BedStatus.AVAILABLE,
    master_data_pb2.BedStatus.OCCUPIED:    BedStatus.OCCUPIED,
    master_data_pb2.BedStatus.CLEANING:    BedStatus.CLEANING,
    master_data_pb2.BedStatus.MAINTENANCE: BedStatus.MAINTENANCE,
}

client_refs = {
    "patient": None,
    "clinical": None,
    "pharmacy": None,
    "laboratory": None,
    "master_data": None,
    "billing": None,
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
    billing_client: BillingClient,
) -> None:
    client_refs["patient"] = patient_client
    client_refs["clinical"] = clinical_client
    client_refs["pharmacy"] = pharmacy_client
    client_refs["laboratory"] = laboratory_client
    client_refs["master_data"] = master_data_client
    client_refs["billing"] = billing_client

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
        token = context.token

        # Parallelise all independent downstream gRPC calls.
        patient_client: PatientClient = client_refs["patient"]
        clinical_client: ClinicalClient = client_refs["clinical"]
        pharmacy_client: PharmacyClient = client_refs["pharmacy"]
        laboratory_client: LaboratoryClient = client_refs["laboratory"]
        billing_client: BillingClient = client_refs["billing"]

        patient_task     = asyncio.create_task(patient_client.get_patient(str(id), metadata))
        encounters_task  = asyncio.create_task(clinical_client.get_encounters(str(id), metadata))
        medications_task = asyncio.create_task(pharmacy_client.get_patient_medications(str(id), metadata))
        lab_task         = asyncio.create_task(laboratory_client.get_patient_lab_history(str(id), metadata))
        billing_task     = asyncio.create_task(billing_client.get_patient_bill(str(id), metadata))

        patient_data, encounters_data, medications_data, lab_data, billing_data = await asyncio.gather(
            patient_task, encounters_task, medications_task, lab_task, billing_task,
            return_exceptions=True,
        )

        if isinstance(patient_data, Exception) or not patient_data:
            # Core patient data is mandatory; abort the entire dashboard on failure.
            return None

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

        billing_summary = None
        if billing_data is not None and not isinstance(billing_data, Exception):
            items_list = [BillItemType(**item) for item in billing_data.get("items", [])]
            billing_summary = BillingSummaryType(
                total_amount=billing_data.get("total_amount", 0.0),
                balance=billing_data.get("balance", 0.0),
                status=billing_data.get("status", ""),
                items=items_list,
            )

        return PatientSummary(
            patient=PatientType(**patient_data),
            encounters=encounters_list,
            medications=medications_list,
            lab_results=lab_results_list,
            billing=billing_summary,
        )

    @strawberry.field
    async def get_reference_data(self, info: Info) -> ReferenceDataSummary:
        context = info.context
        token = context.token
        user_id = context.user_id if hasattr(context, "user_id") else "anonymous"
        
        master_data_client: MasterDataClient = client_refs["master_data"]
        
        # Parallelise top-level reference data fetching
        wards_fut = master_data_client.get_wards(user_id)
        diseases_fut = master_data_client.get_diseases(user_id)
        exams_fut = master_data_client.get_exam_types(user_id)
        ops_fut = master_data_client.get_operation_types(user_id)
        
        wards_raw, diseases_raw, exams_raw, ops_raw = await asyncio.gather(
            wards_fut, diseases_fut, exams_fut, ops_fut
        )
        
        wards_list = []
        for w in wards_raw:
            beds_raw = await master_data_client.get_beds(user_id, w["id"])
            beds = [
                BedType(
                    id=b["id"],
                    code=b["code"],
                    ward_id=b["ward_id"],
                    status=_BED_STATUS_MAP.get(b["status"], BedStatus.AVAILABLE),
                    category=b["category"]
                ) for b in beds_raw
            ]
            
            wards_list.append(WardType(
                id=w["id"],
                code=w["code"],
                name=w["name"],
                beds_count=w["beds_count"],
                is_opd=w["is_opd"],
                beds=beds
            ))

        diseases_list = [DiseaseRefType(**d) for d in diseases_raw]
        exams_list = [ExamTypeRef(**e) for e in exams_raw]
        ops_list = [OperationTypeRef(**o) for o in ops_raw]
        
        return ReferenceDataSummary(
            wards=wards_list,
            diseases=diseases_list,
            exam_types=exams_list,
            operation_types=ops_list
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

    @strawberry.mutation
    async def mark_bed_as_ready(self, info: Info, bed_id: strawberry.ID) -> MarkBedResponse:
        context = info.context
        user_id = context.user_id
        
        master_client: MasterDataClient = client_refs["master_data"]
        # RPC: MarkBedAvailable(BedQuery) returns (BedMessage)
        result = await master_client.mark_bed_available(str(bed_id), user_id)
        
        if result:
            bed_dto = BedType(
                id=result["id"],
                code=result["code"],
                ward_id=result["ward_id"],
                status=_BED_STATUS_MAP.get(result["status"], BedStatus.AVAILABLE),
                category=result.get("category", "")
            )
            return MarkBedResponse(success=True, bed=bed_dto)
        
        return MarkBedResponse(success=False)
