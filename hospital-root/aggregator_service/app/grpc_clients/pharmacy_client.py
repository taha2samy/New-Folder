"""gRPC Client for Pharmacy Service."""

import logging
from typing import Dict, Any, List, Optional
import grpc
from app.generated import pharmacy_pb2, pharmacy_pb2_grpc

logger = logging.getLogger(__name__)

class PharmacyClient:
    def __init__(self, channel: grpc.aio.Channel):
        self.stub = pharmacy_pb2_grpc.PharmacyServiceStub(channel)

    async def get_patient_medications(self, patient_id: str, metadata: tuple) -> Optional[List[Dict[str, Any]]]:
        try:
            req = pharmacy_pb2.PatientMedicationsRequest(patient_id=patient_id)
            # Add trace ID propagation logic per standard
            trace_id = dict(metadata).get("x-trace-id", "unknown")
            metadata = tuple(list(metadata) + [("x-trace-id", trace_id)])
            
            resp = await self.stub.GetPatientMedications(req, metadata=metadata)
            return [
                {
                    "pharmaceutical_id": rec.pharmaceutical_id,
                    "lot_id": rec.lot_id,
                    "quantity": rec.quantity,
                    "date": rec.date,
                }
                for rec in resp.medications
            ]
        except grpc.RpcError as e:
            logger.error(f"gRPC Error GetPatientMedications: {e.details()}")
            return None # Graceful Degradation: return None for partial fails
        except Exception as e:
            logger.error(f"Unexpected Error GetPatientMedications: {e}")
            return None

    async def dispense_medicine(self, pharmaceutical_id: str, quantity: int, patient_id: str, metadata: tuple) -> Optional[Dict[str, Any]]:
        try:
            req = pharmacy_pb2.DispenseRequest(
                pharmaceutical_id=pharmaceutical_id,
                quantity=quantity,
                patient_id=patient_id
            )
            resp = await self.stub.DispenseMedicine(req, metadata=metadata)
            return {
                "success": resp.success,
                "message": resp.message,
                "quantity_dispensed": resp.quantity_dispensed
            }
        except grpc.RpcError as e:
            logger.error(f"gRPC Error DispenseMedicine: {e.details()}")
            raise Exception(f"Pharmacy Error: {e.details()}")
