"""SQLAlchemy ORM domain models for master_data_service.

This service is the Single Source of Truth for all hospital reference/lookup
data. Models are intentionally simple (flat, low-cardinality) to support
high-read workloads with in-memory caching.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def _generate_uuid() -> str:
    """Generate a new UUID4 string suitable for use as a primary key."""
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class ProcedureTypeEnum(str, enum.Enum):
    """Maps to the ProcedureType protobuf enum in master_data.proto."""
    SINGLE_VALUE      = "SINGLE_VALUE"
    MULTIPLE_BOOLEAN  = "MULTIPLE_BOOLEAN"
    MANUAL_TEXT       = "MANUAL_TEXT"


# ---------------------------------------------------------------------------
# Reference Models
# ---------------------------------------------------------------------------

class Ward(Base):
    """
    Represents a hospital department or physical ward.

    is_opd distinguishes Out-Patient Department wards (no bed allocation)
    from in-patient wards.
    """

    __tablename__ = "wards"

    id         = Column(String, primary_key=True, default=_generate_uuid)
    code       = Column(String, unique=True, nullable=False, index=True)
    name       = Column(String, nullable=False)
    beds_count = Column(Integer, nullable=False, default=0)
    is_opd     = Column(Boolean, nullable=False, default=False)
    created_by = Column(String, nullable=True)   # Admin user ID who last modified the record
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=datetime.utcnow)


class DiseaseType(Base):
    """Classification category for ICD disease codes (e.g. Infectious, Chronic)."""

    __tablename__ = "disease_types"

    id   = Column(String, primary_key=True, default=_generate_uuid)
    code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)

    diseases = relationship("Disease", back_populates="disease_type_rel", cascade="all, delete-orphan")


class Disease(Base):
    """
    ICD-style diagnosis code used across clinical encounters.
    disease_type_id is a FK to DiseaseType for grouping.
    """

    __tablename__ = "diseases"

    id              = Column(String, primary_key=True, default=_generate_uuid)
    code            = Column(String, unique=True, nullable=False, index=True)
    description     = Column(Text, nullable=False)
    disease_type_id = Column(String, ForeignKey("disease_types.id"), nullable=False, index=True)
    created_by      = Column(String, nullable=True)
    updated_at      = Column(DateTime(timezone=True), nullable=True, onupdate=datetime.utcnow)

    disease_type_rel = relationship("DiseaseType", back_populates="diseases")


class ExamType(Base):
    """
    Definition of a laboratory examination.

    procedure_type encodes the result format expected by the lab technician:
      1 = Single numeric/text value
      2 = Multiple boolean flags
      3 = Free-form manual text
    """

    __tablename__ = "exam_types"

    id             = Column(String, primary_key=True, default=_generate_uuid)
    code           = Column(String, unique=True, nullable=False, index=True)
    description    = Column(Text, nullable=False)
    procedure_type = Column(
        Enum(ProcedureTypeEnum),
        nullable=False,
        default=ProcedureTypeEnum.SINGLE_VALUE,
    )


class OperationType(Base):
    """
    Surgical or interventional procedure type.
    is_major distinguishes major surgical operations from minor procedures.
    """

    __tablename__ = "operation_types"

    id          = Column(String, primary_key=True, default=_generate_uuid)
    code        = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)
    is_major    = Column(Boolean, nullable=False, default=False)


class Supplier(Base):
    """Pharmaceutical or medical supply vendor registered in the system."""

    __tablename__ = "suppliers"

    id           = Column(String, primary_key=True, default=_generate_uuid)
    name         = Column(String, nullable=False)
    address      = Column(Text, nullable=True)
    contact_info = Column(Text, nullable=True)
