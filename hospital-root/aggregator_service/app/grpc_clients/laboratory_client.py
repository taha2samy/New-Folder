"""Async gRPC client for LaboratoryService.

Wraps the generated stub and projects protobuf responses into plain Python
dictionaries for consumption by the GraphQL layer.  Failures degrade
gracefully and return None so the aggregator can deliver a partial response.
"""

import logging
from typing import Any, Dict, List, Optional

import grpc

from app.generated import laboratory_pb2, laboratory_pb2_grpc

logger = logging.getLogger(__name__)


class LaboratoryClient:
    """Thin async wrapper around the LaboratoryService gRPC stub."""

    def __init__(self, channel: grpc.aio.Channel) -> None:
        self._stub = laboratory_pb2_grpc.LaboratoryServiceStub(channel)

    async def get_patient_lab_history(
        self,
        patient_id: str,
        metadata: tuple,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch all laboratory requests and results for the given patient.

        Returns a list of dicts on success, or None on any RPC or transport error
        (consistent with the graceful-degradation contract used by other clients).
        """
        try:
            request = laboratory_pb2.PatientLabHistoryRequest(patient_id=patient_id)
            response = await self._stub.GetPatientLabHistory(request, metadata=metadata)
            return [
                {
                    "id":                 item.request_id,
                    "test_name":          item.exam_type_id,
                    "status":             laboratory_pb2.TestStatus.Name(item.status),
                    "date":               item.request_date,
                    "result_value":       item.result_value,
                    "result_description": item.result_description,
                }
                for item in response.items
            ]
        except grpc.RpcError as exc:
            logger.error(
                "gRPC error fetching lab history for patient '%s': %s",
                patient_id,
                exc.details(),
            )
            return None
        except Exception as exc:
            logger.error("Unexpected error in LaboratoryClient.get_patient_lab_history: %s", exc)
            return None
