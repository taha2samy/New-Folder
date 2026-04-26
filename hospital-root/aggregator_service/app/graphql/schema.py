"""Strawberry GraphQL definitions for system schemas."""

import strawberry
import enum
from typing import List, Optional


@strawberry.type
class EncounterType:
    encounter_id: str
    status: str
    encounter_type: str
    diagnosis_codes: List[str]
    ward_id: Optional[str] = None
    ward_name: Optional[str] = None
    diagnoses_names: Optional[List[str]] = None

@strawberry.type
class BillItemType:
    description: str
    amount: float
    date: int

@strawberry.type
class BillingSummaryType:
    total_amount: float
    balance: float
    status: str
    items: List[BillItemType]

@strawberry.type
class DiagnosticType:
    id: str
    disease_code: str
    diagnosed_at: str
    notes: str

# ---------------------------------------------------------------------------
# Master Data / Reference Types
# ---------------------------------------------------------------------------

@strawberry.enum
class BedStatus(enum.Enum):
    AVAILABLE   = "AVAILABLE"
    OCCUPIED    = "OCCUPIED"
    CLEANING    = "CLEANING"
    MAINTENANCE = "MAINTENANCE"


@strawberry.type
class BedCategoryType:
    id: str
    name: str
    description: str


@strawberry.type
class BedType:
    id: str
    code: str
    ward_id: str
    status: BedStatus
    category: Optional[BedCategoryType]


@strawberry.type
class WardType:
    id: str
    code: str
    name: str
    beds_count: int
    is_opd: bool
    beds: List[BedType] = strawberry.field(default_factory=list)

@strawberry.type
class DiseaseRefType:
    id: str
    code: str
    description: str
    disease_type: str

@strawberry.type
class ExamTypeRef:
    id: str
    code: str
    description: str
    # Maps directly to Enum integer value on the wire
    procedure_type: int

@strawberry.type
class OperationTypeRef:
    id: str
    code: str
    description: str
    is_major: bool

@strawberry.type
class ReferenceDataSummary:
    wards: List[WardType]
    diseases: List[DiseaseRefType]
    exam_types: List[ExamTypeRef]
    operation_types: List[OperationTypeRef]
    bed_categories: List[BedCategoryType]

@strawberry.type
class PatientType:
    id: str
    code: str
    full_name: str
    birth_date: str
    sex: str
    blood_type: str
    is_insured: bool

@strawberry.type
class MedicationType:
    pharmaceutical_id: str
    lot_id: str
    quantity: int
    date: int

@strawberry.type
class LabResultType:
    """Represents a single laboratory test request and its result (when available)."""
    id:                 str
    test_name:          str           # Maps to exam_type_id
    status:             str
    date:               int           # Unix timestamp of the request
    result_value:       Optional[str]
    result_description: Optional[str]


@strawberry.type
class PatientSummary:
    patient:     Optional[PatientType]
    encounters:  Optional[List[EncounterType]]
    medications: Optional[List[MedicationType]]
    lab_results: Optional[List[LabResultType]]
    billing:     Optional[BillingSummaryType] = None

@strawberry.type
class DispenseResponse:
    success: bool
    message: str
    quantity_dispensed: int

@strawberry.type
class MarkBedResponse:
    success: bool
    bed: Optional[BedType] = None
