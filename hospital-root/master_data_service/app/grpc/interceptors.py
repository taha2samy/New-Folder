"""gRPC server interceptor providing stateless JWT authentication.

Write methods (UpsertWard, UpsertDisease) additionally enforce that the caller
holds the 'admin' role; all read methods require only a valid token.
"""

from typing import Any, Callable

import grpc

from app.core.security import decode_jwt_token

# Methods that require the Admin role in addition to a valid token.
_ADMIN_ONLY_METHODS = frozenset({
    "/master_data.MasterDataService/UpsertWard",
    "/master_data.MasterDataService/UpsertDisease",
})


class AuthInterceptor(grpc.aio.ServerInterceptor):
    """
    Validates JWT tokens on every inbound request and enforces role-based
    access control for write operations.
    """

    async def intercept_service(
        self,
        continuation: Callable,
        handler_call_details: grpc.HandlerCallDetails,
    ) -> Any:
        metadata = dict(handler_call_details.invocation_metadata)

        auth_header = metadata.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return self._abort(
                grpc.StatusCode.UNAUTHENTICATED,
                "Missing or malformed Authorization header.",
            )

        token = auth_header.split(" ", 1)[1]
        decoded = decode_jwt_token(token)

        if not decoded:
            return self._abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid or expired JWT token.")

        user_id = decoded.get("sub")
        role    = decoded.get("role")

        if not user_id or not role:
            return self._abort(
                grpc.StatusCode.UNAUTHENTICATED,
                "JWT token is missing required claims (sub, role).",
            )

        # Enforce Admin-only access for write methods.
        if handler_call_details.method in _ADMIN_ONLY_METHODS and role != "admin":
            return self._abort(
                grpc.StatusCode.PERMISSION_DENIED,
                "This operation is restricted to administrators.",
            )

        # Propagate authenticated claims to the downstream handler.
        enriched_metadata = list(handler_call_details.invocation_metadata)
        enriched_metadata.append(("x-user-id",   str(user_id)))
        enriched_metadata.append(("x-user-role", str(role)))
        enriched_metadata.append(("x-jwt-token", str(token)))

        new_details = grpc.HandlerCallDetails(
            handler_call_details.method,
            tuple(enriched_metadata),
        )

        return await continuation(new_details)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _abort(code: grpc.StatusCode, details: str):
        """Return a synthetic unary handler that immediately aborts with the given status."""

        async def abort_handler(request, context):
            await context.abort(code, details)

        return grpc.unary_unary_rpc_method_handler(abort_handler)
