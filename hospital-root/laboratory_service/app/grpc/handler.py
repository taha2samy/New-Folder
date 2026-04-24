"""gRPC service handler implementing LaboratoryService methods.

All methods are fully asynchronous to support high-concurrency environments.
Business logic delegates to LaboratoryRepository; Kafka events are emitted
after a successful database commit to guarantee at-least-once delivery
semantics aligned with the rest of the HMS platform.
"""

import logging

import grpc

from generated import laboratory_pb2, laboratory_pb2_grpc
from app.domain.repository import (
    DuplicateResultError,
    LabRequestNotFoundError,
    LaboratoryRepository,
)
from app.events.producers import LaboratoryEventProducer
from app.grpc_clients.master_data_client import MasterDataClient

logger = logging.getLogger(__name__)


class LaboratoryServiceHandler(laboratory_pb2_grpc.LaboratoryServiceServicer):
    """Concrete implementation of the LaboratoryService gRPC contract."""

    def __init__(self, db_session_factory, event_producer: LaboratoryEventProducer, master_data_client: MasterDataClient) -> None:
        self._db_session_factory = db_session_factory
        self._event_producer     = event_producer
        self._master_data_client = master_data_client

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_caller(context: grpc.aio.ServicerContext) -> str:
        """
        Extract authenticated caller claims injected by AuthInterceptor.
        Returns user_id.
        """
        metadata = dict(context.invocation_metadata())
        return metadata.get("x-user-id", "")

    @staticmethod
    def _to_timestamp(dt) -> int:
        """Convert a datetime object to a Unix integer timestamp (UTC)."""
        return int(dt.timestamp()) if dt else 0

    # ------------------------------------------------------------------
    # RPC Implementations
    # ------------------------------------------------------------------

    async def CreateLabRequest(self, request, context):
        """
        Initialise a new laboratory test request for a patient.

        Post-commit, a LabRequestCreated event is broadcast to Kafka so that
        billing_service can create the corresponding charge.
        """
        user_id = self._extract_caller(context)
        
        # Extract JWT from context (AuthInterceptor injected it as "authorization" or we can parse ctx)
        metadata = dict(context.invocation_metadata())
        raw_auth = metadata.get("authorization", "")
        token = raw_auth.split("Bearer ")[-1] if "Bearer " in raw_auth else ""
        if not token: token = metadata.get("x-jwt-token", "")

        # Validate Exam Type checks against Master Data System
        exam_types_list = await self._master_data_client.get_exam_types(token)
        exam_type_ids = {et["id"] for et in exam_types_list}
        if request.exam_type_id not in exam_type_ids:
             await context.abort(grpc.StatusCode.NOT_FOUND, f"ExamType {request.exam_type_id} does not exist.")

        try:
            async with self._db_session_factory() as session:
                async with session.begin():   # Atomic transaction
                    repo = LaboratoryRepository(session)
                    lab_request = await repo.create_lab_request(
                        patient_id=request.patient_id,
                        exam_type_id=request.exam_type_id,
                        material=request.material,
                        admission_id=request.admission_id or None,
                    )

            # Event emitted AFTER successful commit — prevents phantom events.
            self._event_producer.broadcast_lab_request_created(
                patient_id=lab_request.patient_id,
                exam_type_id=lab_request.exam_type_id,
                request_id=lab_request.id,
            )

            logger.info(
                "LabRequest created: id=%s patient=%s exam_type=%s initiated_by=%s",
                lab_request.id,
                lab_request.patient_id,
                lab_request.exam_type_id,
                user_id,
            )

            return laboratory_pb2.LabRequestResponse(
                request_id=lab_request.id,
                patient_id=lab_request.patient_id,
                exam_type_id=lab_request.exam_type_id,
                material=lab_request.material,
                status=laboratory_pb2.TestStatus.Value(lab_request.status.value),
                request_date=self._to_timestamp(lab_request.request_date),
            )

        except grpc.RpcError:
            raise
        except Exception as exc:
            logger.exception("CreateLabRequest unhandled error: %s", exc)
            await context.abort(grpc.StatusCode.INTERNAL, "An internal error occurred while creating the lab request.")

    async def SubmitResults(self, request, context):
        """
        Record the technical results produced by a laboratory technician.

        Pydantic validation of the value format occurs before the database write.
        A LabResultCompleted event is emitted post-commit to trigger downstream
        notification workflows.
        """
        try:
            async with self._db_session_factory() as session:
                async with session.begin():
                    repo = LaboratoryRepository(session)
                    lab_result = await repo.create_lab_result(
                        request_id=request.request_id,
                        description=request.description,
                        value=request.value,
                        technician_id=request.technician_id,
                    )
                    # Capture parent fields before session closes.
                    patient_id   = lab_result.request.patient_id
                    exam_type_id = lab_result.request.exam_type_id

            self._event_producer.broadcast_lab_result_completed(
                patient_id=patient_id,
                request_id=lab_result.request_id,
                exam_type_id=exam_type_id,
                technician_id=lab_result.technician_id,
            )

            logger.info(
                "LabResult submitted: result_id=%s request_id=%s technician=%s",
                lab_result.id,
                lab_result.request_id,
                lab_result.technician_id,
            )

            return laboratory_pb2.LabResultResponse(
                result_id=lab_result.id,
                request_id=lab_result.request_id,
                description=lab_result.description,
                value=lab_result.value,
                technician_id=lab_result.technician_id,
                result_date=self._to_timestamp(lab_result.result_date),
            )

        except LabRequestNotFoundError as exc:
            await context.abort(grpc.StatusCode.NOT_FOUND, str(exc))
        except DuplicateResultError as exc:
            await context.abort(grpc.StatusCode.ALREADY_EXISTS, str(exc))
        except grpc.RpcError:
            raise
        except Exception as exc:
            logger.exception("SubmitResults unhandled error: %s", exc)
            await context.abort(grpc.StatusCode.INTERNAL, "An internal error occurred while submitting results.")

    async def GetPatientLabHistory(self, request, context):
        """
        Return the complete laboratory history for a patient.

        Results are projected into LabHistoryItem messages; the result fields
        are populated only when the associated LabRequest status is COMPLETED.
        """
        try:
            async with self._db_session_factory() as session:
                repo = LaboratoryRepository(session)
                requests = await repo.get_patient_lab_history(request.patient_id)

            items = []
            for lab_req in requests:
                item = laboratory_pb2.LabHistoryItem(
                    request_id=lab_req.id,
                    exam_type_id=lab_req.exam_type_id,
                    material=lab_req.material,
                    status=laboratory_pb2.TestStatus.Value(lab_req.status.value),
                    request_date=self._to_timestamp(lab_req.request_date),
                )
                if lab_req.result:
                    item.result_value       = lab_req.result.value
                    item.result_description = lab_req.result.description
                    item.result_date        = self._to_timestamp(lab_req.result.result_date)

                items.append(item)

            return laboratory_pb2.PatientLabHistoryResponse(
                patient_id=request.patient_id,
                items=items,
            )

        except grpc.RpcError:
            raise
        except Exception as exc:
            logger.exception("GetPatientLabHistory unhandled error: %s", exc)
            await context.abort(grpc.StatusCode.INTERNAL, "An internal error occurred while retrieving lab history.")
