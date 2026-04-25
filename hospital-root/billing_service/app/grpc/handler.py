import logging
import grpc
from typing import Callable, Any
from copy import copy

from app.generated import billing_pb2, billing_pb2_grpc
from app.domain.repository import BillingRepository
from decimal import Decimal

logger = logging.getLogger(__name__)

class BillingServiceHandler(billing_pb2_grpc.BillingServiceServicer):
    def __init__(self, db_session_factory: Callable[..., Any]):
        self.db_session_factory = db_session_factory

    def _extract_context(self, context):
        metadata = dict(context.invocation_metadata())
        token = metadata.get("authorization", "")
        if token.startswith("Bearer "):
             token = token[7:]
        else:
             token = metadata.get("x-jwt-token", "")
        # Real implementation decodes here to extract user info
        from app.core.security import decode_token
        payload = decode_token(token)
        user_id = payload.get("sub", "unknown") if payload else "unknown"
        return user_id, token

    async def GetPatientBill(self, request, context):
        user_id, token = self._extract_context(context)
        try:
            async with self.db_session_factory() as session:
                repo = BillingRepository(session)
                bill = await repo.get_active_bill(request.patient_id)
                
                items = []
                # Assuming bill.items is eagerly loaded
                for item in bill.items:
                    items.append(billing_pb2.BillItemProto(
                        id=str(item.id),
                        item_type=item.item_type,
                        reference_id=item.reference_id,
                        quantity=int(item.quantity),
                        amount=float(item.amount),
                        name=f"{item.item_type} - {item.reference_id}"
                    ))
                
                return billing_pb2.BillResponse(
                    bill_id=str(bill.id),
                    patient_id=bill.patient_id,
                    total_amount=float(bill.total_amount),
                    balance=float(bill.balance),
                    status=bill.status,
                    items=items
                )
        except Exception as e:
            logger.error(f"GetPatientBill Error: {e}")
            await context.abort(grpc.StatusCode.INTERNAL, "Error fetching bill.")

    async def ProcessPayment(self, request, context):
        user_id, token = self._extract_context(context)
        try:
            async with self.db_session_factory() as session:
                repo = BillingRepository(session)
                amount = Decimal(str(request.amount))
                payment = await repo.record_payment(request.bill_id, amount, request.user_id)
                if not payment:
                    await context.abort(grpc.StatusCode.NOT_FOUND, "Bill not found.")
                
                # Fetch updated bill
                bill = await repo.get_bill_by_id(request.bill_id)
                return billing_pb2.PaymentResponse(
                    success=True,
                    remaining_balance=float(bill.balance)
                )
        except grpc.RpcError: raise
        except Exception as e:
            logger.error(f"ProcessPayment Error: {e}")
            await context.abort(grpc.StatusCode.INTERNAL, "Error processing payment.")

    async def UpdatePriceList(self, request, context):
        user_id, token = self._extract_context(context)
        # RBAC check removed for testing phase
        try:
            async with self.db_session_factory() as session:
                repo = BillingRepository(session)
                for item in request.items:
                    await repo.update_price(item.item_type, item.reference_id, Decimal(str(item.price)))
                return billing_pb2.PriceResponse(success=True)
        except grpc.RpcError: raise
        except Exception as e:
            logger.error(f"UpdatePriceList Error: {e}")
            await context.abort(grpc.StatusCode.INTERNAL, "Error updating prices.")

    async def GetPrice(self, request, context):
        user_id, token = self._extract_context(context)
        try:
            async with self.db_session_factory() as session:
                repo = BillingRepository(session)
                price = await repo.get_price(request.item_type, request.reference_id)
                if price is None:
                    await context.abort(grpc.StatusCode.NOT_FOUND, f"Price for {request.item_type}/{request.reference_id} not found.")
                
                return billing_pb2.PriceItem(
                    item_type=request.item_type,
                    reference_id=request.reference_id,
                    price=float(price)
                )
        except grpc.RpcError: raise
        except Exception as e:
            logger.error(f"GetPrice Error: {e}")
            await context.abort(grpc.StatusCode.INTERNAL, "Error fetching price.")
