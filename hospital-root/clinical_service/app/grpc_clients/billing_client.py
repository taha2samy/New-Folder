import grpc
import logging
from app.generated import billing_pb2, billing_pb2_grpc

logger = logging.getLogger(__name__)

class BillingClient:
    def __init__(self, address: str):
        self.channel = grpc.aio.insecure_channel(address)
        self.stub = billing_pb2_grpc.BillingServiceStub(self.channel)

    async def get_price(self, item_type: str, reference_id: str, token: str):
        metadata = (('authorization', f'Bearer {token}'),)
        try:
            request = billing_pb2.PriceQuery(item_type=item_type, reference_id=reference_id)
            response = await self.stub.GetPrice(request, metadata=metadata)
            return response.price
        except grpc.RpcError as e:
            logger.error(f"Error calling BillingService.GetPrice: {e.code()} - {e.details()}")
            return None

    async def close(self):
        await self.channel.close()
