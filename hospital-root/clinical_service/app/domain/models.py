"""Domain models for clinical encounters."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, ForeignKey, DateTime, func, Boolean, Integer
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Encounter(Base):
    __tablename__ = "encounters"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), nullable=False, index=True)
    doctor_id = Column(String(36), nullable=False, index=True)
    encounter_type = Column(String(20), nullable=False) # OPD, ADMISSION
    status = Column(String(20), nullable=False, default="ACTIVE") # ACTIVE, COMPLETED, SUSPENDED
    ward_id = Column(String(50), nullable=True)
    bed_number = Column(String(20), nullable=True)
    notes = Column(String, nullable=True)
    
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    vitals = relationship("VitalSign", back_populates="encounter", uselist=False, cascade="all, delete-orphan")
    diagnoses = relationship("Diagnosis", back_populates="encounter", cascade="all, delete-orphan")


class VitalSign(Base):
    __tablename__ = "vital_signs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    encounter_id = Column(String(36), ForeignKey("encounters.id"), nullable=False, unique=True)
    blood_pressure_systolic = Column(Float, nullable=True)
    blood_pressure_diastolic = Column(Float, nullable=True)
    heart_rate = Column(Float, nullable=True)
    temperature_celsius = Column(Float, nullable=True)
    spo2 = Column(Float, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

    encounter = relationship("Encounter", back_populates="vitals")


class Diagnosis(Base):
    __tablename__ = "diagnoses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    encounter_id = Column(String(36), ForeignKey("encounters.id"), nullable=False)
    disease_id = Column(String(50), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    encounter = relationship("Encounter", back_populates="diagnoses")

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), nullable=False, index=True)
    doctor_id = Column(String(36), nullable=False, index=True)
    ward_id = Column(String(50), nullable=True)
    scheduled_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(20), nullable=False, default="SCHEDULED") # SCHEDULED, CANCELLED
    is_deleted = Column(Boolean, default=False, nullable=False)

class SurgerySchedule(Base):
    __tablename__ = "surgery_schedules"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), nullable=False, index=True)
    operation_type_id = Column(String(50), nullable=False)
    theater_id = Column(String(50), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    estimated_duration_min = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="SCHEDULED") # SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED
    is_deleted = Column(Boolean, default=False, nullable=False)
