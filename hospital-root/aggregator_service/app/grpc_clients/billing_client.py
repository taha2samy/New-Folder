"""gRPC async wrapper for BillingService."""

import grpc
import logging
from typing import Optional, Dict, Any
from app.generated import billing_pb2, billing_pb2_grpc

logger = logging.getLogger(__name__)

class BillingClient:
    def __init__(self, channel: grpc.aio.Channel):
        self.stub = billing_pb2_grpc.BillingServiceStub(channel)

    async def get_patient_bill(self, patient_id: str, metadata: tuple) -> Optional[Dict[str, Any]]:
        try:
            request = billing_pb2.BillRequest(patient_id=patient_id)
            response = await self.stub.GetPatientBill(request, metadata=metadata)
            return {
                "total_amount": response.total_amount,
                "balance": response.balance,
                "status": response.status,
                "items": [
                    {
                        "description": item.name,
                        "amount": item.amount,
                        "date": 0
                    }
                    for item in response.items
                ]
            }
        except grpc.RpcError as e:
            logger.error(f"gRPC BillingRequest failed: {e}")
            return None

    async def update_price_list(self, items: list[dict], metadata: tuple) -> bool:
        try:
            proto_items = [
                billing_pb2.PriceItem(
                    item_type=i["item_type"],
                    reference_id=i["reference_id"],
                    price=i["price"]
                ) for i in items
            ]
            request = billing_pb2.PriceRequest(items=proto_items)
            response = await self.stub.UpdatePriceList(request, metadata=metadata)
            return response.success
        except grpc.RpcError as e:
            logger.error(f"gRPC UpdatePriceList failed: {e}")
            return False
