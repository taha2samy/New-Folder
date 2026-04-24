entries (x-user-id, x-jwt-token) to the downstream handler.
"""

from typing import Any, Callable

import grpc

from app.core.security import decode_jwt_token


class AuthInterceptor(grpc.aio.ServerInterceptor):
    """Reject unauthenticated or unauthorised requests before they reach the handler."""

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

        if not user_id:
            return self._abort(
                grpc.StatusCode.UNAUTHENTICATED,
                "JWT token is missing required search claim (sub).",
            )

        # Propagate claims to the handler via request metadata.
        enriched_metadata = list(handler_call_details.invocation_metadata)
        enriched_metadata.append(("x-user-id",    str(user_id)))
        enriched_metadata.append(("x-user-id",    str(user_id)))
        enriched_metadata.append(("x-jwt-token",  str(token)))

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
