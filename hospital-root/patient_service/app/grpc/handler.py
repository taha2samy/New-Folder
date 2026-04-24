"""gRPC handler for PatientService."""

import logging
import functools
import grpc
from datetime import datetime, timezone
from generated import patient_pb2, patient_pb2_grpc
from app.domain.repository import PatientRepository
from app.domain.models import Patient
from app.events.producers import EventProducer

logger = logging.getLogger(__name__)



class PatientServiceHandler(patient_pb2_grpc.PatientServiceServicer):
    """
    Implements the PatientService gRPC contract.
    """
    def __init__(self, db_session_factory, event_producer: EventProducer):
        self.db_session_factory = db_session_factory
        self.event_producer = event_producer

    def _extract_context(self, context: grpc.aio.ServicerContext):
        """Extracts injected metadata."""
        metadata = dict(context.invocation_metadata())
        user_id = metadata.get("x-user-id", "")
        trace_id = metadata.get("x-trace-id", "unknown")
        return user_id, trace_id

    async def GetPatientById(self, request, context):
        user_id, _, trace_id = self._extract_context(context)
        logger.info(f"[Trace: {trace_id}] User {user_id} requested patient {request.id}")

        try:
            async with self.db_session_factory() as session:
                repo = PatientRepository(session)
                patient = await repo.get_by_id(request.id)
                
                if not patient:
                    await context.abort(grpc.StatusCode.NOT_FOUND, "Patient not found or access denied.")
                
                return self._map_to_proto(patient)
        except grpc.RpcError:
            raise
        except Exception as e:
            logger.error(f"Error fetching patient: {e}")
            await context.abort(grpc.StatusCode.INTERNAL, "Internal system error.")

    async def CreatePatient(self, request, context):
        user_id, _, trace_id = self._extract_context(context)
        logger.info(f"[Trace: {trace_id}] User {user_id} creating patient {request.code}")

        try:
            async with self.db_session_factory() as session:
                repo = PatientRepository(session)
                patient = Patient(
                    code=request.code,
                    full_name=request.full_name,
                    birth_date=request.birth_date,
                    sex=patient_pb2.Sex.Name(request.sex),
                    blood_type=request.blood_type,
                    is_insured=request.is_insured
                )
                
                created_patient = await repo.create(patient)
                
                # Fire and forget Kafka event
                self.event_producer.broadcast_patient_registered(
                    patient_id=created_patient.id,
                    hospital_code=created_patient.code,
                    timestamp=datetime.now(timezone.utc).isoformat()
                )

                return self._map_to_proto(created_patient)
        except Exception as e:
            logger.error(f"Error creating patient: {e}")
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Failed to create patient.")

    async def UpdatePatient(self, request, context):
        user_id, _, trace_id = self._extract_context(context)
        logger.info(f"[Trace: {trace_id}] User {user_id} updating patient {request.id}")

        try:
            async with self.db_session_factory() as session:
                repo = PatientRepository(session)
                patient = await repo.get_by_id(request.id)
                if not patient:
                    await context.abort(grpc.StatusCode.NOT_FOUND, "Patient not found.")
                
                patient.full_name = request.full_name
                patient.birth_date = request.birth_date
                patient.sex = patient_pb2.Sex.Name(request.sex)
                patient.blood_type = request.blood_type
                patient.is_insured = request.is_insured
                
                updated_patient = await repo.update(patient)
                
                return self._map_to_proto(updated_patient)
        except grpc.RpcError:
             raise
        except Exception as e:
            logger.error(f"Error updating patient: {e}")
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Failed to update patient.")

    async def ListPatients(self, request, context):
        user_id, _, trace_id = self._extract_context(context)
        
        try:
            async with self.db_session_factory() as session:
                repo = PatientRepository(session)
                patients = await repo.list_patients(request.limit, request.offset)
                
                response = patient_pb2.PatientListResponse(total_count=len(patients))
                for p in patients:
                    response.patients.append(self._map_to_proto(p))
                return response
        except Exception as e:
            logger.error(f"Error listing patients: {e}")
            await context.abort(grpc.StatusCode.INTERNAL, "Failed to list patients.")

    def _map_to_proto(self, patient: Patient) -> patient_pb2.PatientResponse:
        sex_enum_value = getattr(patient_pb2.Sex, str(patient.sex).upper(), patient_pb2.Sex.UNKNOWN)
        return patient_pb2.PatientResponse(
            id=patient.id,
            code=patient.code,
            full_name=patient.full_name,
            birth_date=patient.birth_date,
            sex=sex_enum_value,
            blood_type=patient.blood_type or "",
            is_insured=patient.is_insured
        )
