"""SQLAlchemy ORM domain models for laboratory_service."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def _generate_uuid() -> str:
    """Generate a new UUID4 string suitable for use as a primary key."""
    return str(uuid.uuid4())


class TestStatus(str, enum.Enum):
    """Lifecycle status of a laboratory test request."""

    PENDING   = "PENDING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class LabRequest(Base):
    """
    Represents a clinician-initiated request for a laboratory examination.

    The is_deleted flag implements a soft-delete pattern so that financial and
    audit records referencing this entity remain intact after logical removal.
    """

    __tablename__ = "lab_requests"

    id            = Column(String, primary_key=True, default=_generate_uuid)
    patient_id    = Column(String, nullable=False, index=True)
    admission_id  = Column(String, nullable=True)           # Present for in-patient admissions only
    exam_type_id  = Column(String, nullable=False, index=True)
    material      = Column(String, nullable=False)           # Sample type, e.g. Blood, Urine, Tissue
    status        = Column(
        Enum(TestStatus),
        nullable=False,
        default=TestStatus.PENDING,
    )
    request_date  = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    is_deleted    = Column(Boolean, nullable=False, default=False)  # Soft-delete flag for audit trails

    result = relationship(
        "LabResult",
        back_populates="request",
        uselist=False,
        cascade="all, delete-orphan",
    )


class LabResult(Base):
    """
    Stores the technical result produced by a laboratory technician.

    The value field is stored as plain text to accommodate all three result
    formats defined in the User Guide:
      - Single numeric value (e.g. "7.4")
      - Multiple boolean flags (e.g. JSON-serialised list)
      - Free-form manual text narrative
    """

    __tablename__ = "lab_results"

    id            = Column(String, primary_key=True, default=_generate_uuid)
    request_id    = Column(
        String,
        ForeignKey("lab_requests.id"),
        nullable=False,
        unique=True,   # One result record per request
        index=True,
    )
    description   = Column(Text, nullable=False)             # Human-readable interpretation
    value         = Column(Text, nullable=False)             # Raw result value (format-agnostic)
    result_date   = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    technician_id = Column(String, nullable=False)

    request = relationship("LabRequest", back_populates="result")
