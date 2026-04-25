"""gRPC Handlers for Clinical Encounters."""

import logging
import functools
import grpc
from app.generated import clinical_pb2, clinical_pb2_grpc, master_data_pb2
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
        return metadata.get("x-user-id", ""), metadata.get("x-jwt-token", ""), metadata.get("x-trace-id", "unknown")

    async def _validate_patient(self, patient_id: str, jwt_token: str, context: grpc.aio.ServicerContext):
        patient = await self.patient_client.get_patient_by_id(patient_id, jwt_token)
        if not patient or patient['status'] == 'deleted':
            await context.abort(grpc.StatusCode.FAILED_PRECONDITION, f"Patient {patient_id} not found or deleted limit.")
        return patient

    async def CreateOPDVisit(self, request, context):
        user_id, _, token, trace_id = self._extract_context(context)
        logger.info(f"AUDIT - User:{user_id} | Action:CreateOPDVisit")
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
                            temperature_celsius=request.vitals.temperature_celsius,
                            spo2=request.vitals.spo2
                        )
                    await repo.create_encounter(encounter)
                    
            self.event_producer.broadcast_encounter_created(encounter.id, encounter.patient_id, encounter.encounter_type)
            return self._map_to_proto(encounter)
        except Exception as e:
            logger.error(f"OPD Error: {e}")
            await context.abort(grpc.StatusCode.INTERNAL, "Error creating OPD.")

    async def StartAdmission(self, request, context):
        user_id, _, token, trace_id = self._extract_context(context)
        logger.info(f"AUDIT - User:{user_id} | Action:StartAdmission")
        logger.info(f"[Trace: {trace_id}] User {user_id} starting Admission for {request.patient_id}")
        await self._validate_patient(request.patient_id, token, context)

        # Validate Bed status via Master Data Service
        if request.ward_id and request.bed_id:
            beds_list = await self.master_data_client.get_beds_by_ward(request.ward_id, token)
            selected_bed = next((b for b in beds_list if b["id"] == request.bed_id), None)
            
            if not selected_bed:
                await context.abort(grpc.StatusCode.NOT_FOUND, f"Bed {request.bed_id} not found in Ward {request.ward_id}.")
            
            if selected_bed["status"] != master_data_pb2.BedStatus.AVAILABLE:
                await context.abort(grpc.StatusCode.FAILED_PRECONDITION, f"Bed {request.bed_id} is not AVAILABLE (Status: {selected_bed['status']}).")

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
                        ward_id=request.ward_id,
                        bed_id=request.bed_id
                    )
                    await repo.create_encounter(encounter)
            
            # Atomic Operation: Update bed status to OCCUPIED
            await self.master_data_client.update_bed_status(request.bed_id, master_data_pb2.BedStatus.OCCUPIED, token)
            
            self.event_producer.broadcast_bed_status_changed(request.bed_id, "OCCUPIED", request.ward_id)
                    
            self.event_producer.broadcast_encounter_created(encounter.id, encounter.patient_id, encounter.encounter_type, request.bed_id)
            return self._map_to_proto(encounter)
        except grpc.RpcError: raise
        except Exception as e:
            logger.error(f"Admission Error: {e}")
            await context.abort(grpc.StatusCode.INTERNAL, "Error starting admission.")

    async def CompleteEncounter(self, request, context):
        user_id, _, token, trace_id = self._extract_context(context)
        logger.info(f"AUDIT - User:{user_id} | Action:CompleteEncounter")
        
        # Validate Disease IDs against Master Data Service
        if request.diagnoses_ids:
            diseases_list = await self.master_data_client.get_diseases(token)
            valid_disease_ids = {d["id"] for d in diseases_list}
            for code in request.diagnoses_ids:
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
                    for dx_id in request.diagnoses_ids:
                        encounter.diagnoses.append(Diagnosis(disease_id=dx_id))
                        
            self.event_producer.broadcast_encounter_completed(encounter.id, encounter.patient_id)
            
            # Automatically trigger bed cleaning if it was an admission
            if encounter.encounter_type == "ADMISSION" and encounter.bed_id:
                await self.master_data_client.update_bed_status(encounter.bed_id, master_data_pb2.BedStatus.CLEANING, token)
                self.event_producer.broadcast_bed_status_changed(encounter.bed_id, "CLEANING", encounter.ward_id)

            return self._map_to_proto(encounter)
        except grpc.RpcError: raise
        except Exception as e:
            logger.error(f"Complete Encounter Error: {e}")
            await context.abort(grpc.StatusCode.INTERNAL, "Error completing encounter.")

    async def GetPatientEncounters(self, request, context):
        user_id, _, token, trace_id = self._extract_context(context)
        logger.info(f"AUDIT - User:{user_id} | Action:GetPatientEncounters")
        try:
            async with self.db_session_factory() as session:
                repo = ClinicalRepository(session)
                encounters = await repo.get_patient_encounters(request.patient_id)
                for enc in encounters:
                    yield self._map_to_proto(enc)
        except Exception as e:
            logger.error(f"Stream Error: {e}")
            await context.abort(grpc.StatusCode.INTERNAL, "Error streaming.")

    async def CreateAppointment(self, request, context):
        user_id, _, token, trace_id = self._extract_context(context)
        logger.info(f"AUDIT - User:{user_id} | Action:CreateAppointment")
        logger.info(f"[Trace: {trace_id}] User {user_id} creating appointment for {request.patient_id}")
        # Note: Actual repository injection of Appointment domain model would happen here
        return clinical_pb2.AppointmentResponse(id="sched-mock", status="SCHEDULED")

    async def ScheduleSurgery(self, request, context):
        user_id, _, token, trace_id = self._extract_context(context)
        logger.info(f"AUDIT - User:{user_id} | Action:ScheduleSurgery")
        logger.info(f"[Trace: {trace_id}] User {user_id} scheduling surgery for {request.patient_id}")
        return clinical_pb2.SurgeryResponse(id="surg-mock", status="SCHEDULED")

    async def RecordSurgery(self, request, context):
        user_id, _, token, trace_id = self._extract_context(context)
        logger.info(f"AUDIT - User:{user_id} | Action:RecordSurgery")
        logger.info(f"[Trace: {trace_id}] User {user_id} recording surgery {request.surgery_id}")
        return clinical_pb2.SurgeryResponse(id=request.surgery_id, status="COMPLETED")

    async def GetActiveAdmissions(self, request, context):
        """Returns a stream of all active admissions for billing/housekeeping."""
        try:
            async with self.db_session_factory() as session:
                repo = ClinicalRepository(session)
                admissions = await repo.get_active_admissions()
                for adm in admissions:
                    yield self._map_to_proto(adm)
        except Exception as e:
            logger.error(f"GetActiveAdmissions Error: {e}")
            await context.abort(grpc.StatusCode.INTERNAL, "Error streaming active admissions.")

    def _map_to_proto(self, encounter: Encounter) -> clinical_pb2.EncounterResponse:
        return clinical_pb2.EncounterResponse(
            encounter_id=encounter.id,
            patient_id=encounter.patient_id,
            doctor_id=encounter.doctor_id,
            status=encounter.status,
            encounter_type=encounter.encounter_type,
            created_at=int(encounter.created_at.timestamp() if encounter.created_at else 0),
            diagnoses_ids=[d.disease_id for d in encounter.diagnoses] if getattr(encounter, "diagnoses", None) else [],
            ward_id=encounter.ward_id if getattr(encounter, "ward_id", None) else "",
            spo2=encounter.vitals.spo2 if getattr(encounter, "vitals", None) and encounter.vitals.spo2 else 0.0,
            bed_id=encounter.bed_id if getattr(encounter, "bed_id", None) else ""
        )
