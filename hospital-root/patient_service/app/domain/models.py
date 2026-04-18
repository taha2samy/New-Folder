"""Domain models for patient_service."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Patient(Base):
    """
    Patient domain entity mapped to 'patients' table.
    """
    __tablename__ = "patients"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(20), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    birth_date = Column(String(10), nullable=False)  # ISO format YYYY-MM-DD
    sex = Column(String(10), nullable=False) # Maps to proto Sex enum strings
    blood_type = Column(String(5), nullable=True)
    is_insured = Column(Boolean, default=False)
    
    is_deleted = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
