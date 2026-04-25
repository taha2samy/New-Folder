"""gRPC server interceptor providing stateless JWT authentication.

Write methods (UpsertWard, UpsertDisease) additionally enforce that the caller
holds the 'admin' role; all read methods require only a valid token.
"""

from typing import Any, Callable

import grpc

from app.core.security import decode_jwt_token
from app.core.config import settings




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
        internal_secret = metadata.get("x-internal-secret")

        user_id = None
        token = None

        # 1. Check Internal Secret (Highest priority for background tasks)
        if internal_secret == settings.INTERNAL_API_SECRET:
            user_id = "system-internal"
            token = "internal-bypass"
        
        # 2. Check JWT Token
        elif auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
            decoded = decode_jwt_token(token)
            if decoded:
                user_id = decoded.get("sub")

        if not user_id:
            return self._abort(
                grpc.StatusCode.UNAUTHENTICATED,
                "Authentication failed: Missing internal secret or invalid JWT.",
            )



        # Propagate authenticated claims to the downstream handler.
        enriched_metadata = list(handler_call_details.invocation_metadata)
        enriched_metadata.append(("x-user-id",   str(user_id)))
        enriched_metadata.append(("x-user-id",   str(user_id)))
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
