from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from .models import Bill, BillItem, PriceList, Payment
from decimal import Decimal

class BillingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_active_bill(self, patient_id: str) -> Bill:
        result = await self.session.execute(
            select(Bill)
            .options(selectinload(Bill.items), selectinload(Bill.payments))
            .where(Bill.patient_id == patient_id, Bill.status == "OPEN")
        )
        bill = result.scalars().first()
        if not bill:
            bill = Bill(patient_id=patient_id, status="OPEN")
            self.session.add(bill)
            await self.session.commit()
            await self.session.refresh(bill)
        return bill

    async def get_bill_by_id(self, bill_id: str) -> Bill:
        result = await self.session.execute(
            select(Bill)
            .options(selectinload(Bill.items), selectinload(Bill.payments))
            .where(Bill.id == bill_id)
        )
        return result.scalars().first()

    async def get_price(self, item_type: str, reference_id: str) -> Decimal:
        result = await self.session.execute(
            select(PriceList).where(PriceList.item_type == item_type, PriceList.reference_id == reference_id)
        )
        pl = result.scalars().first()
        return pl.price if pl else None

    async def add_bill_item(self, patient_id: str, item_type: str, reference_id: str, quantity: Decimal, amount: Decimal) -> BillItem:
        bill = await self.get_active_bill(patient_id)

        # Check idempotency: Did we already add this reference ID to this bill?
        # Note: If multiple dispensing of same medical_id happens, they might have different trace IDs, 
        # but the prompt says: "Idempotency: Ensure that processing the same Kafka event twice does not result in duplicate billing (check ReferenceID before insertion)."
        # In our case, the reference_id passed here will be combining the event ID or similar if we want true idempotency, or we allow duplicate medical_ids but different request_ids.
        # Let's ensure reference_id is treated as idempotency key per bill!
        # E.g. reference_id = "MedicineDispensed-<timestamp>" or "request_id".
        existing_result = await self.session.execute(
            select(BillItem).where(BillItem.bill_id == bill.id, BillItem.reference_id == reference_id)
        )
        if existing_result.scalars().first():
            return None # Already processed

        new_item = BillItem(
            bill_id=bill.id,
            item_type=item_type,
            reference_id=reference_id,
            quantity=quantity,
            amount=amount
        )
        self.session.add(new_item)
        
        bill.total_amount += amount
        bill.balance += amount
        
        await self.session.commit()
        return new_item

    async def record_payment(self, bill_id: str, amount: Decimal, user_id: str) -> Payment:
        bill = await self.get_bill_by_id(bill_id)
        if not bill:
            return None

        payment = Payment(
            bill_id=bill.id,
            amount=amount,
            user_id=user_id
        )
        self.session.add(payment)
        
        bill.balance -= amount
        if bill.balance <= 0:
            bill.status = "CLOSED"
            
        await self.session.commit()
        return payment

    async def update_price(self, item_type: str, reference_id: str, price: Decimal) -> PriceList:
        result = await self.session.execute(
            select(PriceList).where(PriceList.item_type == item_type, PriceList.reference_id == reference_id)
        )
        pl = result.scalars().first()
        if pl:
            pl.price = price
        else:
            pl = PriceList(item_type=item_type, reference_id=reference_id, price=price)
            self.session.add(pl)
        await self.session.commit()
        return pl
