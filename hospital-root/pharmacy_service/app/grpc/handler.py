"""gRPC Handlers for Pharmacy Service."""

import logging
import grpc
from datetime import datetime
from generated import pharmacy_pb2, pharmacy_pb2_grpc
from app.domain.repository import PharmacyRepository, InadequateStockError
from app.events.producers import PharmacyEventProducer

logger = logging.getLogger(__name__)

class PharmacyServiceHandler(pharmacy_pb2_grpc.PharmacyServiceServicer):
    def __init__(self, db_session_factory, event_producer: PharmacyEventProducer):
        self.db_session_factory = db_session_factory
        self.event_producer = event_producer

    def _extract_context(self, context: grpc.aio.ServicerContext):
        metadata = dict(context.invocation_metadata())
        return metadata.get("x-user-id", ""), metadata.get("x-user-role", ""), metadata.get("x-jwt-token", "")

    async def GetStockLevel(self, request, context):
        try:
            async with self.db_session_factory() as session:
                repo = PharmacyRepository(session)
                
                # Check if pharmaceutical exists
                # In a real scenario we'd first search by code or id appropriately.
                # Assuming request.pharmaceutical_id is the code or id. Let's try code first, then fallback or just id.
                pharma = await repo.get_pharmaceutical(request.pharmaceutical_id)
                if not pharma:
                    pharma = await repo.get_pharmaceutical_by_code(request.pharmaceutical_id)
                
                if not pharma:
                    await context.abort(grpc.StatusCode.NOT_FOUND, "Pharmaceutical not found.")

                total_stock = await repo.get_total_stock(pharma.id)
                
                is_critical = total_stock <= pharma.critical_level
                
                return pharmacy_pb2.StockResponse(
                    pharmaceutical_id=pharma.id,
                    total_available_quantity=total_stock,
                    is_critical=is_critical
                )
        except grpc.RpcError: raise
        except Exception as e:
            logger.error(f"GetStockLevel Error: {e}")
            await context.abort(grpc.StatusCode.INTERNAL, "Error retrieving stock level.")

    async def AddStock(self, request, context):
        user_id, role, token = self._extract_context(context)
        try:
            expiry_dt = datetime.strptime(request.expiry_date, "%Y-%m-%d")
        except ValueError:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Invalid date format. Use YYYY-MM-DD.")
            
        try:
            async with self.db_session_factory() as session:
                async with session.begin(): # ACID Transaction
                    repo = PharmacyRepository(session)
                    
                    pharma = await repo.get_pharmaceutical(request.pharmaceutical_id)
                    if not pharma:
                        pharma = await repo.get_pharmaceutical_by_code(request.pharmaceutical_id)
                    
                    if not pharma:
                        await context.abort(grpc.StatusCode.NOT_FOUND, "Pharmaceutical not found.")

                    lot = await repo.add_stock(
                        pharma_id=pharma.id,
                        lot_code=request.lot_code,
                        expiry_date=expiry_dt,
                        quantity=request.quantity,
                        unit_cost=request.unit_cost,
                        user_id=user_id
                    )
                    
                return pharmacy_pb2.AddStockResponse(
                    success=True,
                    lot_id=lot.id
                )
        except grpc.RpcError: raise
        except Exception as e:
            logger.error(f"AddStock Error: {e}")
            await context.abort(grpc.StatusCode.INTERNAL, "Error adding stock.")

    async def DispenseMedicine(self, request, context):
        user_id, role, token = self._extract_context(context)
        try:
            dispensed_details = []
            async with self.db_session_factory() as session:
                async with session.begin(): # ACID Transaction
                    repo = PharmacyRepository(session)
                    
                    pharma = await repo.get_pharmaceutical(request.pharmaceutical_id)
                    if not pharma:
                        pharma = await repo.get_pharmaceutical_by_code(request.pharmaceutical_id)

                    if not pharma:
                        await context.abort(grpc.StatusCode.NOT_FOUND, "Pharmaceutical not found.")

                    dispensed_details = await repo.dispense_medicine(
                        pharma_id=pharma.id,
                        quantity_to_dispense=request.quantity,
                        patient_id=request.patient_id,
                        user_id=user_id
                    )
            
            # Emit Kafka Event explicitly after successful commit
            for detail in dispensed_details:
                self.event_producer.broadcast_medicine_dispensed(
                    patient_id=request.patient_id,
                    medical_id=request.pharmaceutical_id,
                    quantity_dispensed=detail['quantity'],
                    unit_cost=detail['unit_cost']
                )

            return pharmacy_pb2.DispenseResponse(
                success=True,
                message="Successfully dispensed via FEFO.",
                quantity_dispensed=request.quantity
            )
        except InadequateStockError as e:
            logger.warning(f"Failed to dispense: {e}")
            await context.abort(grpc.StatusCode.FAILED_PRECONDITION, str(e))
        except grpc.RpcError: raise
        except Exception as e:
            logger.error(f"DispenseMedicine Error: {e}")
            await context.abort(grpc.StatusCode.INTERNAL, "Error dispensing medicine.")

    async def GetPatientMedications(self, request, context):
        user_id, role, token = self._extract_context(context)
        try:
            async with self.db_session_factory() as session:
                repo = PharmacyRepository(session)
                movements = await repo.get_patient_medications(request.patient_id)
                
                records = []
                for mv in movements: # SQLAlchemy lazy loading concerns: usually we should join eager load 'lot'
                    # But since we only need the lot_id directly from StockMovement and pharmaceutical_id is in lot..
                    # Let's assume we ensure lot eager loading or just use lot_id. Wait, MedicalLot ID is in movement.lot_id.
                    # We might need to fetch the pharmaceutical_id via eager load if we want it, but let's query it or extract if eager loaded.
                    # This simplest way:
                    records.append(
                        pharmacy_pb2.MedicationRecord(
                            pharmaceutical_id=mv.lot.pharmaceutical_id if mv.lot else "unknown",
                            lot_id=mv.lot_id,
                            quantity=mv.quantity,
                            date=int(mv.date.timestamp()) if mv.date else 0
                        )
                    )
                    
                return pharmacy_pb2.PatientMedicationsResponse(
                    patient_id=request.patient_id,
                    medications=records
                )
        except grpc.RpcError: raise
        except Exception as e:
            logger.error(f"GetPatientMedications Error: {e}")
            await context.abort(grpc.StatusCode.INTERNAL, "Error retrieving patient medications.")
