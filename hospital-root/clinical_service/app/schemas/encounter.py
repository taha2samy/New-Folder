"""Pydantic schemas for validating Domain models before DB insert."""

from pydantic import BaseModel, Field
from typing import Optional

class VitalsSchema(BaseModel):
    blood_pressure_systolic: float = Field(..., gt=0, lt=300)
    blood_pressure_diastolic: float = Field(..., gt=0, lt=200)
    heart_rate: float = Field(..., gt=0, lt=300)
    temperature_celsius: float = Field(..., gt=20, lt=45)

class CreateOPDVisitSchema(BaseModel):
    patient_id: str
    doctor_id: str
    notes: Optional[str] = None
    vitals: Optional[VitalsSchema] = None

class StartAdmissionSchema(BaseModel):
    patient_id: str
    doctor_id: str
    ward_id: str
    bed_id: str
