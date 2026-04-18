"""Domain models for Pharmacy Service."""

from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import uuid
import enum

Base = declarative_base()

def generate_uuid():
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

    lots = relationship("MedicalLot", back_populates="pharmaceutical", cascade="all, delete-orphan")

class MedicalLot(Base):
    __tablename__ = "medical_lots"

    id = Column(String, primary_key=True, default=generate_uuid)
    pharmaceutical_id = Column(String, ForeignKey("pharmaceuticals.id"), nullable=False)
    lot_code = Column(String, unique=True, index=True, nullable=False)
    expiry_date = Column(DateTime(timezone=True), nullable=False)
    quantity = Column(Integer, default=0, nullable=False)
    unit_cost = Column(Float, nullable=False)

    pharmaceutical = relationship("Pharmaceutical", back_populates="lots")
    movements = relationship("StockMovement", back_populates="lot", cascade="all, delete-orphan")

class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(String, primary_key=True, default=generate_uuid)
    lot_id = Column(String, ForeignKey("medical_lots.id"), nullable=False)
    date = Column(DateTime(timezone=True), default=datetime.utcnow)
    type = Column(Enum(MovementType), nullable=False)
    quantity = Column(Integer, nullable=False)
    patient_id = Column(String, nullable=True) # Only populated on DISCHARGE
    user_id = Column(String, nullable=False)   # Who initiated the movement?

    lot = relationship("MedicalLot", back_populates="movements")
