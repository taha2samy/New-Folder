import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Bill(Base):
    __tablename__ = "bills"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, nullable=False, index=True)
    total_amount = Column(Numeric(10, 2), default=0.00, nullable=False)
    balance = Column(Numeric(10, 2), default=0.00, nullable=False)
    status = Column(String, default="OPEN", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = relationship("BillItem", back_populates="bill", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="bill", cascade="all, delete-orphan")

class BillItem(Base):
    __tablename__ = "bill_items"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    bill_id = Column(String, ForeignKey("bills.id"), nullable=False)
    item_type = Column(String, nullable=False) # DRUG, PROCEDURE, ENCOUNTER, ADMISSION
    reference_id = Column(String, nullable=False)
    quantity = Column(Numeric(10, 4), default=1.0)
    amount = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    bill = relationship("Bill", back_populates="items")

class PriceList(Base):
    __tablename__ = "price_list"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    item_type = Column(String, nullable=False)
    reference_id = Column(String, nullable=False, unique=True)
    price = Column(Numeric(10, 2), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Payment(Base):
    __tablename__ = "payments"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    bill_id = Column(String, ForeignKey("bills.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    user_id = Column(String, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)

    bill = relationship("Bill", back_populates="payments")
