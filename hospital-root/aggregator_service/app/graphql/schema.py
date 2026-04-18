"""Strawberry GraphQL definitions for system schemas."""

import strawberry
from typing import List, Optional

@strawberry.type
class EncounterType:
    encounter_id: str
    status: str
    encounter_type: str
    diagnosis_codes: List[str]

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
class PatientSummary:
    patient: Optional[PatientType]
    encounters: Optional[List[EncounterType]]
