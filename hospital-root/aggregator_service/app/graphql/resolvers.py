"""GraphQL Resolvers and parallel orchestration."""

import asyncio
import time
import logging
from typing import List, Optional

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
    BedCategoryType,
)
from app.generated import master_data_pb2
from app.grpc_clients.clinical_client import ClinicalClient
from app.grpc_clients.laboratory_client import LaboratoryClient
from app.grpc_clients.patient_client import PatientClient
from app.grpc_clients.pharmacy_client import PharmacyClient
from app.grpc_clients.master_data_client import MasterDataClient
from app.grpc_clients.billing_client import BillingClient

logger = logging.getLogger(__name__)

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
        await _get_cached_master_data(master_data_client, metadata)

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
        metadata = context.metadata
        
        master_data_client: MasterDataClient = client_refs["master_data"]
        
        # Parallelise top-level reference data fetching
        wards_fut = master_data_client.get_wards(metadata)
        diseases_fut = master_data_client.get_diseases(metadata)
        exams_fut = master_data_client.get_exam_types(metadata)
        ops_fut = master_data_client.get_operation_types(metadata)
        beds_fut = master_data_client.get_all_beds(metadata) # Batch fetch all beds
        
        wards_raw, diseases_raw, exams_raw, ops_raw, all_beds_raw = await asyncio.gather(
            wards_fut, diseases_fut, exams_fut, ops_fut, beds_fut
        )

        # Map beds to wards in-memory (O(N))
        beds_by_ward = {}
        for b in all_beds_raw:
            w_id = b["ward_id"]
            if w_id not in beds_by_ward:
                beds_by_ward[w_id] = []
            beds_by_ward[w_id].append(
                BedType(
                    id=b["id"],
                    code=b["code"],
                    ward_id=b["ward_id"],
                    status=_BED_STATUS_MAP.get(b["status"], BedStatus.AVAILABLE),
                    category=b["category"]
                )
            )
        
        wards_list = []
        for w in wards_raw:
            ward_id = w["id"]
            beds = beds_by_ward.get(ward_id, [])
            
            wards_list.append(WardType(
                id=ward_id,
                code=w["code"],
                name=w["name"],
                beds_count=w["beds_count"],
                is_opd=w["is_opd"],
                beds=beds
            ))

        diseases_list = [DiseaseRefType(**d) for d in diseases_raw]
        exams_list = [ExamTypeRef(**e) for e in exams_raw]
        ops_list = [OperationTypeRef(**o) for o in ops_raw]
        
        # Sequentially fetch for now to not break gather format
        bed_cats_raw = await master_data_client.get_bed_categories(metadata)
        bed_cats_list = [BedCategoryType(**c) for c in bed_cats_raw]
        
        return ReferenceDataSummary(
            wards=wards_list,
            diseases=diseases_list,
            exam_types=exams_list,
            operation_types=ops_list,
            bed_categories=bed_cats_list
        )

    @strawberry.field
    async def get_bed_categories(self, info: Info) -> List[BedCategoryType]:
        context = info.context
        metadata = context.metadata
        
        master_data_client: MasterDataClient = client_refs["master_data"]
        bed_cats_raw = await master_data_client.get_bed_categories(metadata)
        return [BedCategoryType(**c) for c in bed_cats_raw]

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
        metadata = context.metadata
        token = context.token
        user_id = context.user_id
        
        master_client: MasterDataClient = client_refs["master_data"]
        # RPC: MarkBedAsReady(BedQuery) returns (BedMessage)
        result = await master_client.mark_bed_as_ready(str(bed_id), metadata)
        
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

    @strawberry.mutation
    async def upsert_exam_type(
        self,
        info: Info,
        code: str,
        description: str,
        procedure_type: int,
        exam_type_id: Optional[str] = None
    ) -> Optional[ExamTypeRef]:
        """Create or update an examination type via master_data_service."""
        context = info.context
        metadata = context.metadata
        
        master_client: MasterDataClient = client_refs["master_data"]
        result = await master_client.upsert_exam_type(
            code=code,
            description=description,
            procedure_type=procedure_type,
            metadata=metadata,
            exam_type_id=exam_type_id
        )
        if result:
            return ExamTypeRef(**result)
        return None

    @strawberry.mutation
    async def upsert_operation_type(
        self,
        info: Info,
        code: str,
        description: str,
        is_major: bool,
        operation_type_id: Optional[str] = None
    ) -> Optional[OperationTypeRef]:
        """Create or update an operation type via master_data_service."""
        context = info.context
        metadata = context.metadata
        
        master_client: MasterDataClient = client_refs["master_data"]
        result = await master_client.upsert_operation_type(
            code=code,
            description=description,
            is_major=is_major,
            metadata=metadata,
            operation_type_id=operation_type_id
        )
        if result:
            return OperationTypeRef(**result)
        return None

    @strawberry.mutation
    async def upsert_bed_category(
        self,
        info: Info,
        name: str,
        description: str,
        price: Optional[float] = None,
        id: Optional[str] = None
    ) -> Optional[BedCategoryType]:
        """Create or update a bed category, and sync pricing."""
        context = info.context
        metadata = context.metadata
        
        master_client: MasterDataClient = client_refs["master_data"]
        billing_client: BillingClient = client_refs["billing"]
        
        # Fire master data upsert
        cat_task = asyncio.create_task(master_client.upsert_bed_category(
            name=name,
            description=description,
            metadata=metadata,
            id=id
        ))
        
        # Concurrently fire billing orchestrator if price is specified
        bill_task = None
        if price is not None:
            bill_task = asyncio.create_task(billing_client.update_price_list(
                items=[{
                    "item_type": "ADMISSION",
                    "reference_id": name,
                    "price": price
                }],
                metadata=metadata
            ))
            
        cat_res = await cat_task
        if bill_task:
            await bill_task
            
        if cat_res:
            return BedCategoryType(**cat_res)
        return None

    @strawberry.mutation
    async def upsert_bed(
        self,
        info: Info,
        code: str,
        ward_id: str,
        category_id: str,
        status: int,
        bed_id: Optional[str] = None,
    ) -> BedType:
        logger.info(f"Received upsert_bed request from frontend for code {code}")
        
        md_client = info.context["clients"]["master_data"]
        res = await md_client.upsert_bed(
            bed_id=bed_id,
            code=code,
            ward_id=ward_id,
            category_id=category_id,
            status=status,
            metadata=info.context["grpc_metadata"]
        )
        
        if not res:
            raise Exception("Failed to upsert bed in master data service.")
            
        category_msg = None
        if res.get("category"):
            category_msg = BedCategoryType(
                id=res["category"]["id"],
                name=res["category"]["name"],
                description=res["category"]["description"],
            )

        return BedType(
            id=res["id"],
            code=res["code"],
            ward_id=res["ward_id"],
            status=res["status"],
            category=category_msg,
        )
