"""gRPC Handlers for Clinical Encounters."""

import logging
import grpc
from generated import clinical_pb2, clinical_pb2_grpc
from app.domain.repository import ClinicalRepository
from app.domain.models import Encounter, VitalSign, Diagnosis
from app.events.producers import EncounterEventProducer
from app.grpc_clients.patient_client import PatientServiceClient
from app.grpc_clients.master_data_client import MasterDataClient

logger = logging.getLogger(__name__)

class ClinicalEncounterServiceHandler(clinical_pb2_grpc.ClinicalEncounterServiceServicer):
    def __init__(self, db_session_factory, event_producer: EncounterEventProducer, patient_client: PatientServiceClient, master_data_client: MasterDataClient):
        self.db_session_factory = db_session_factory
        self.event_producer = event_producer
        self.patient_client = patient_client
        self.master_data_client = master_data_client

    def _extract_context(self, context: grpc.aio.ServicerContext):
        metadata = dict(context.invocation_metadata())
        return metadata.get("x-user-id", ""), metadata.get("x-user-role", ""), metadata.get("x-jwt-token", ""), metadata.get("x-trace-id", "unknown")

    async def _validate_patient(self, patient_id: str, jwt_token: str, context: grpc.aio.ServicerContext):
        patient = await self.patient_client.get_patient_by_id(patient_id, jwt_token)
        if not patient or patient['status'] == 'deleted':
            await context.abort(grpc.StatusCode.FAILED_PRECONDITION, f"Patient {patient_id} not found or deleted limit.")
        return patient

    async def CreateOPDVisit(self, request, context):
        user_id, role, token, trace_id = self._extract_context(context)
        logger.info(f"[Trace: {trace_id}] User {user_id} creating OPD for {request.patient_id}")
        await self._validate_patient(request.patient_id, token, context)

        try:
            async with self.db_session_factory() as session:
                async with session.begin():
                    repo = ClinicalRepository(session)
                    encounter = Encounter(
                        patient_id=request.patient_id,
                        doctor_id=request.doctor_id,
                        encounter_type="OPD",
                        notes=request.notes
                    )
                    if request.HasField('vitals'):
                        encounter.vitals = VitalSign(
                            blood_pressure_systolic=request.vitals.blood_pressure_systolic,
                            blood_pressure_diastolic=request.vitals.blood_pressure_diastolic,
                            heart_rate=request.vitals.heart_rate,
                            temperature_celsius=request.vitals.temperature_celsius
                        )
                    await repo.create_encounter(encounter)
                    
            self.event_producer.broadcast_encounter_created(encounter.id, encounter.patient_id, encounter.encounter_type)
            return self._map_to_proto(encounter)
        except Exception as e:
            logger.error(f"OPD Error: {e}")
            await context.abort(grpc.StatusCode.INTERNAL, "Error creating OPD.")

    async def StartAdmission(self, request, context):
        user_id, role, token, trace_id = self._extract_context(context)
        logger.info(f"[Trace: {trace_id}] User {user_id} starting Admission for {request.patient_id}")
        await self._validate_patient(request.patient_id, token, context)

        # Validate Ward ID against Master Data Service
        if request.ward:
            wards_list = await self.master_data_client.get_wards(token)
            ward_ids = {w["id"] for w in wards_list}
            if request.ward not in ward_ids:
                await context.abort(grpc.StatusCode.FAILED_PRECONDITION, f"Ward {request.ward} does not exist.")

        try:
            async with self.db_session_factory() as session:
                repo = ClinicalRepository(session)
                if await repo.has_active_admission(request.patient_id):
                    await context.abort(grpc.StatusCode.ALREADY_EXISTS, "Patient already admitted.")
                
                async with session.begin():
                    encounter = Encounter(
                        patient_id=request.patient_id,
                        doctor_id=request.doctor_id,
                        encounter_type="ADMISSION",
                        ward=request.ward,
                        bed_number=request.bed_number
                    )
                    await repo.create_encounter(encounter)
                    
            self.event_producer.broadcast_encounter_created(encounter.id, encounter.patient_id, encounter.encounter_type)
            return self._map_to_proto(encounter)
        except grpc.RpcError: raise
        except Exception as e:
            logger.error(f"Admission Error: {e}")
            await context.abort(grpc.StatusCode.INTERNAL, "Error starting admission.")

    async def CompleteEncounter(self, request, context):
        user_id, role, token, trace_id = self._extract_context(context)
        
        # Validate Disease IDs against Master Data Service
        if request.diagnosis_codes:
            diseases_list = await self.master_data_client.get_diseases(token)
            valid_disease_ids = {d["id"] for d in diseases_list}
            for code in request.diagnosis_codes:
                if code not in valid_disease_ids:
                     await context.abort(grpc.StatusCode.FAILED_PRECONDITION, f"Diagnosis Code {code} does not exist.")
        
        try:
            async with self.db_session_factory() as session:
                repo = ClinicalRepository(session)
                encounter = await repo.get_encounter_by_id(request.encounter_id)
                if not encounter:
                    await context.abort(grpc.StatusCode.NOT_FOUND, "Encounter not found.")

                async with session.begin():
                    encounter.status = "COMPLETED"
                    for dx_code in request.diagnosis_codes:
                        encounter.diagnoses.append(Diagnosis(code=dx_code))
                        
            self.event_producer.broadcast_encounter_completed(encounter.id, encounter.patient_id)
            return self._map_to_proto(encounter)
        except grpc.RpcError: raise
        except Exception as e:
            logger.error(f"Complete Encounter Error: {e}")
            await context.abort(grpc.StatusCode.INTERNAL, "Error completing encounter.")

    async def GetPatientEncounters(self, request, context):
        user_id, role, token, trace_id = self._extract_context(context)
        try:
            async with self.db_session_factory() as session:
                repo = ClinicalRepository(session)
                encounters = await repo.get_patient_encounters(request.patient_id, user_id, role)
                for enc in encounters:
                    yield self._map_to_proto(enc)
        except Exception as e:
            logger.error(f"Stream Error: {e}")
            await context.abort(grpc.StatusCode.INTERNAL, "Error streaming.")

    def _map_to_proto(self, encounter: Encounter) -> clinical_pb2.EncounterResponse:
        return clinical_pb2.EncounterResponse(
            encounter_id=encounter.id,
            patient_id=encounter.patient_id,
            doctor_id=encounter.doctor_id,
            status=encounter.status,
            encounter_type=encounter.encounter_type,
            created_at=int(encounter.created_at.timestamp() if encounter.created_at else 0),
            diagnosis_codes=[d.code for d in encounter.diagnoses] if getattr(encounter, "diagnoses", None) else []
        )
