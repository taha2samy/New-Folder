"""gRPC service handler implementing MasterDataService methods.

All read methods apply an asyncio-safe in-process TTL cache (via a simple
timestamp-based invalidation) to eliminate repetitive database round-trips
for data that changes infrequently.  Write methods flush the relevant cache
partition after committing the transaction.
"""

import asyncio
import logging
import time
from typing import Any, Dict, Optional

import grpc

from app.generated import master_data_pb2, master_data_pb2_grpc
from app.domain.models import ProcedureTypeEnum
from app.domain.repository import EntityNotFoundError, MasterDataRepository
from app.events.producers import MasterDataEventProducer

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Simple TTL In-Memory Cache
# ---------------------------------------------------------------------------
# Structure: { cache_key: (payload, expiry_monotonic_ts) }
_CACHE_TTL_SECONDS = 60  # Reference data is considered fresh for 60 seconds
_cache: Dict[str, tuple[Any, float]] = {}
_cache_lock = asyncio.Lock()


def _cache_get(key: str) -> Optional[Any]:
    entry = _cache.get(key)
    if entry and time.monotonic() < entry[1]:
        return entry[0]
    return None


def _cache_set(key: str, value: Any) -> None:
    _cache[key] = (value, time.monotonic() + _CACHE_TTL_SECONDS)


def _cache_invalidate(key: str) -> None:
    _cache.pop(key, None)


# ---------------------------------------------------------------------------
# Proto enum helpers
# ---------------------------------------------------------------------------

_PROCEDURE_TYPE_MAP = {
    ProcedureTypeEnum.SINGLE_VALUE:     master_data_pb2.ProcedureType.SINGLE_VALUE,
    ProcedureTypeEnum.MULTIPLE_BOOLEAN: master_data_pb2.ProcedureType.MULTIPLE_BOOLEAN,
    ProcedureTypeEnum.MANUAL_TEXT:      master_data_pb2.ProcedureType.MANUAL_TEXT,
}


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------

class MasterDataServiceHandler(master_data_pb2_grpc.MasterDataServiceServicer):
    """Concrete implementation of the MasterDataService gRPC contract."""

    def __init__(self, db_session_factory, event_producer: MasterDataEventProducer) -> None:
        self._db_session_factory = db_session_factory
        self._event_producer     = event_producer

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_caller(self, context: grpc.aio.ServicerContext) -> str:
        """Extract authenticated caller claims injected by AuthInterceptor."""
        metadata = dict(context.invocation_metadata())
        return metadata.get("x-user-id", "")

    # ------------------------------------------------------------------
    # Read RPCs
    # ------------------------------------------------------------------

    async def GetWards(self, request, context):
        async with _cache_lock:
            cached = _cache_get("wards")
            if cached:
                return cached

        try:
            async with self._db_session_factory() as session:
                repo  = MasterDataRepository(session)
                wards = await repo.get_all_wards()

            response = master_data_pb2.WardsResponse(
                wards=[
                    master_data_pb2.WardMessage(
                        ward_id=w.id,
                        code=w.code,
                        name=w.name,
                        beds_count=w.beds_count,
                        is_opd=w.is_opd,
                    )
                    for w in wards
                ]
            )
            async with _cache_lock:
                _cache_set("wards", response)
            return response

        except grpc.RpcError:
            raise
        except Exception as exc:
            logger.exception("GetWards error: %s", exc)
            await context.abort(grpc.StatusCode.INTERNAL, "Error retrieving wards.")

    async def GetDiseases(self, request, context):
        search_term = (request.search_term or "").strip()
        cache_key   = f"diseases:{search_term}"

        async with _cache_lock:
            cached = _cache_get(cache_key)
            if cached:
                return cached

        try:
            async with self._db_session_factory() as session:
                repo     = MasterDataRepository(session)
                diseases = await repo.get_all_diseases(search_term)

            response = master_data_pb2.DiseasesResponse(
                diseases=[
                    master_data_pb2.DiseaseMessage(
                        disease_id=d.id,
                        code=d.code,
                        description=d.description,
                        disease_type=d.disease_type_rel.code if d.disease_type_rel else "",
                    )
                    for d in diseases
                ]
            )
            async with _cache_lock:
                _cache_set(cache_key, response)
            return response

        except grpc.RpcError:
            raise
        except Exception as exc:
            logger.exception("GetDiseases error: %s", exc)
            await context.abort(grpc.StatusCode.INTERNAL, "Error retrieving diseases.")

    async def GetExamTypes(self, request, context):
        async with _cache_lock:
            cached = _cache_get("exam_types")
            if cached:
                return cached

        try:
            async with self._db_session_factory() as session:
                repo       = MasterDataRepository(session)
                exam_types = await repo.get_all_exam_types()

            response = master_data_pb2.ExamTypesResponse(
                exam_types=[
                    master_data_pb2.ExamTypeMessage(
                        exam_type_id=et.id,
                        code=et.code,
                        description=et.description,
                        procedure_type=_PROCEDURE_TYPE_MAP.get(
                            et.procedure_type,
                            master_data_pb2.ProcedureType.PROCEDURE_TYPE_UNSPECIFIED,
                        ),
                    )
                    for et in exam_types
                ]
            )
            async with _cache_lock:
                _cache_set("exam_types", response)
            return response

        except grpc.RpcError:
            raise
        except Exception as exc:
            logger.exception("GetExamTypes error: %s", exc)
            await context.abort(grpc.StatusCode.INTERNAL, "Error retrieving exam types.")

    async def GetOperationTypes(self, request, context):
        async with _cache_lock:
            cached = _cache_get("operation_types")
            if cached:
                return cached

        try:
            async with self._db_session_factory() as session:
                repo            = MasterDataRepository(session)
                operation_types = await repo.get_all_operation_types()

            response = master_data_pb2.OperationTypesResponse(
                operation_types=[
                    master_data_pb2.OperationTypeMessage(
                        operation_type_id=ot.id,
                        code=ot.code,
                        description=ot.description,
                        is_major=ot.is_major,
                    )
                    for ot in operation_types
                ]
            )
            async with _cache_lock:
                _cache_set("operation_types", response)
            return response

        except grpc.RpcError:
            raise
        except Exception as exc:
            logger.exception("GetOperationTypes error: %s", exc)
            await context.abort(grpc.StatusCode.INTERNAL, "Error retrieving operation types.")

    async def GetSuppliers(self, request, context):
        async with _cache_lock:
            cached = _cache_get("suppliers")
            if cached:
                return cached

        try:
            async with self._db_session_factory() as session:
                repo      = MasterDataRepository(session)
                suppliers = await repo.get_all_suppliers()

            response = master_data_pb2.SuppliersResponse(
                suppliers=[
                    master_data_pb2.SupplierMessage(
                        supplier_id=s.id,
                        name=s.name,
                        address=s.address or "",
                        contact_info=s.contact_info or "",
                    )
                    for s in suppliers
                ]
            )
            async with _cache_lock:
                _cache_set("suppliers", response)
            return response

        except grpc.RpcError:
            raise
        except Exception as exc:
            logger.exception("GetSuppliers error: %s", exc)
            await context.abort(grpc.StatusCode.INTERNAL, "Error retrieving suppliers.")

    # ------------------------------------------------------------------
    # Write RPCs (Admin-only — enforced by AuthInterceptor)
    # ------------------------------------------------------------------

    async def UpsertWard(self, request, context):
        """Create or update a Ward record and broadcast a cache-invalidation event."""
        user_id = self._extract_caller(context)
        is_create   = not request.ward_id

        try:
            async with self._db_session_factory() as session:
                async with session.begin():
                    repo = MasterDataRepository(session)
                    ward = await repo.upsert_ward(
                        ward_id=request.ward_id or None,
                        code=request.code,
                        name=request.name,
                        beds_count=request.beds_count,
                        is_opd=request.is_opd,
                        admin_id=user_id,
                    )

            # Invalidate the ward list cache after successful commit.
            async with _cache_lock:
                _cache_invalidate("wards")

            self._event_producer.broadcast_reference_data_changed(
                entity_type="WARD",
                action="CREATE" if is_create else "UPDATE",
                admin_id=user_id,
                entity_id=ward.id,
            )
            logger.info(
                "Ward %s by user=%s: id=%s code=%s",
                "created" if is_create else "updated",
                user_id,
                ward.id,
                ward.code,
            )

            return master_data_pb2.WardMessage(
                ward_id=ward.id,
                code=ward.code,
                name=ward.name,
                beds_count=ward.beds_count,
                is_opd=ward.is_opd,
            )

        except EntityNotFoundError as exc:
            await context.abort(grpc.StatusCode.NOT_FOUND, str(exc))
        except grpc.RpcError:
            raise
        except Exception as exc:
            logger.exception("UpsertWard error: %s", exc)
            await context.abort(grpc.StatusCode.INTERNAL, "Error upserting ward.")

    async def UpsertDisease(self, request, context):
        """Create or update a Disease record and broadcast a cache-invalidation event."""
        user_id = self._extract_caller(context)
        is_create   = not request.disease_id

        try:
            async with self._db_session_factory() as session:
                async with session.begin():
                    repo    = MasterDataRepository(session)
                    disease = await repo.upsert_disease(
                        disease_id=request.disease_id or None,
                        code=request.code,
                        description=request.description,
                        disease_type_code=request.disease_type,
                        admin_id=user_id,
                    )

            # Invalidate all disease cache entries.
            async with _cache_lock:
                keys_to_drop = [k for k in _cache if k.startswith("diseases:")]
                for k in keys_to_drop:
                    _cache_invalidate(k)

            self._event_producer.broadcast_reference_data_changed(
                entity_type="DISEASE",
                action="CREATE" if is_create else "UPDATE",
                admin_id=user_id,
                entity_id=disease.id,
            )
            logger.info(
                "Disease %s by user=%s: id=%s code=%s",
                "created" if is_create else "updated",
                user_id,
                disease.id,
                disease.code,
            )

            return master_data_pb2.DiseaseMessage(
                disease_id=disease.id,
                code=disease.code,
                description=disease.description,
                disease_type=request.disease_type,
            )

        except EntityNotFoundError as exc:
            await context.abort(grpc.StatusCode.NOT_FOUND, str(exc))
        except grpc.RpcError:
            raise
        except Exception as exc:
            logger.exception("UpsertDisease error: %s", exc)
            await context.abort(grpc.StatusCode.INTERNAL, "Error upserting disease.")
