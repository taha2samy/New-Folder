"""Domain models for Pharmacy Service."""

import uuid
import enum
from decimal import Decimal
from datetime import datetime

from sqlalchemy import Column, Integer, String, Numeric, DateTime, Enum, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def generate_uuid() -> str:
    return str(uuid.uuid4())


class MovementType(str, enum.Enum):
    CHARGE = "CHARGE"
    DISCHARGE = "DISCHARGE"


class Pharmaceutical(Base):
    __tablename__ = "pharmaceuticals"

    id = Column(String, primary_key=True, default=generate_uuid)
    code = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=False)
    critical_level = Column(Integer, default=10, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    lots = relationship("MedicalLot", back_populates="pharmaceutical", cascade="all, delete-orphan")


class MedicalLot(Base):
    __tablename__ = "medical_lots"

    id = Column(String, primary_key=True, default=generate_uuid)
    # FK to Pharmaceutical; named medical_id per spec
    medical_id = Column(String, ForeignKey("pharmaceuticals.id"), nullable=False)
    lot_code = Column(String, unique=True, index=True, nullable=False)
    expiry_date = Column(DateTime(timezone=True), nullable=False)
    quantity = Column(Integer, default=0, nullable=False)
    unit_cost = Column(Numeric(10, 4), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    pharmaceutical = relationship("Pharmaceutical", back_populates="lots", foreign_keys=[medical_id])
    movements = relationship("StockMovement", back_populates="lot", cascade="all, delete-orphan")


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(String, primary_key=True, default=generate_uuid)
    medical_id = Column(String, ForeignKey("pharmaceuticals.id"), nullable=False)
    lot_id = Column(String, ForeignKey("medical_lots.id"), nullable=False)
    type = Column(Enum(MovementType), nullable=False)
    quantity = Column(Integer, nullable=False)
    patient_id = Column(String, nullable=True)   # only on DISCHARGE
    actor_id = Column(String, nullable=False)     # pharmacist who performed the action
    date = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    lot = relationship("MedicalLot", back_populates="movements")
