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

def require_roles(allowed_roles):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, request, context):
            user_id, roles_str, trace_id = self._extract_context(context)
            user_roles = [r.strip() for r in roles_str.split(",") if r.strip()]
            
            has_access = any(r in user_roles for r in allowed_roles)
            if not has_access:
                await context.abort(
                    grpc.StatusCode.PERMISSION_DENIED, 
                    f"Security: User lacks required role {allowed_roles}"
                )
            return await func(self, request, context)
        return wrapper
    return decorator

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
        roles = metadata.get("x-user-roles", "")
        trace_id = metadata.get("x-trace-id", "unknown")
        return user_id, roles, trace_id

    @require_roles(["PATIENT_VIEW", "ADMIN", "PATIENT"])
    async def GetPatientById(self, request, context):
        user_id, roles_str, trace_id = self._extract_context(context)
        user_roles = [r.strip() for r in roles_str.split(",") if r.strip()]
        logger.info(f"[Trace: {trace_id}] User {user_id} requested patient {request.id}")
        
        # Row-Level Security explicitly checked
        if len(user_roles) == 1 and "PATIENT" in user_roles:
            if request.id != user_id:
                await context.abort(grpc.StatusCode.PERMISSION_DENIED, "Security: User lacks required role [PATIENT Access Violation]")
            pseudo_role = "patient"
        else:
            pseudo_role = "admin"

        try:
            async with self.db_session_factory() as session:
                repo = PatientRepository(session)
                patient = await repo.get_by_id(request.id, pseudo_role, user_id)
                
                if not patient:
                    await context.abort(grpc.StatusCode.NOT_FOUND, "Patient not found or access denied.")
                
                return self._map_to_proto(patient)
        except grpc.RpcError:
            raise
        except Exception as e:
            logger.error(f"Error fetching patient: {e}")
            await context.abort(grpc.StatusCode.INTERNAL, "Internal system error.")

    @require_roles(["PATIENT_CREATE", "ADMIN"])
    async def CreatePatient(self, request, context):
        user_id, roles_str, trace_id = self._extract_context(context)
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

    @require_roles(["PATIENT_EDIT", "ADMIN"])
    async def UpdatePatient(self, request, context):
        user_id, roles_str, trace_id = self._extract_context(context)
        logger.info(f"[Trace: {trace_id}] User {user_id} updating patient {request.id}")

        try:
            async with self.db_session_factory() as session:
                repo = PatientRepository(session)
                patient = await repo.get_by_id(request.id, "admin", user_id)
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

    @require_roles(["PATIENT_VIEW", "ADMIN"])
    async def ListPatients(self, request, context):
        user_id, roles_str, trace_id = self._extract_context(context)
        
        try:
            async with self.db_session_factory() as session:
                repo = PatientRepository(session)
                pseudo_role = "admin"
                patients = await repo.list_patients(request.limit, request.offset, pseudo_role, user_id)
                
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
