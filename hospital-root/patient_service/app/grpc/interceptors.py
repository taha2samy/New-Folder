"""gRPC interceptors for patient_service."""

import grpc
from typing import Callable, Any
from app.core.security import decode_jwt_token

class AuthInterceptor(grpc.aio.ServerInterceptor):
    """
    Validates JWT and injects user_id and role into context.
    """

    async def intercept_service(
        self,
        continuation: Callable,
        handler_call_details: grpc.HandlerCallDetails
    ) -> Any:
        """
        Intercepts the gRPC call to check authorization.
        """
        metadata = dict(handler_call_details.invocation_metadata)
        auth_header = metadata.get("authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return self._abort(grpc.StatusCode.UNAUTHENTICATED, "Missing or invalid authorization header.")

        token = auth_header.split(" ")[1]
        decoded = decode_jwt_token(token)

        if not decoded:
            return self._abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid or expired token.")

        user_id = decoded.get("sub")
        if not user_id:
            return self._abort(grpc.StatusCode.UNAUTHENTICATED, "Token missing required claims.")

        # Pass metadata dynamically by appending to invocation metadata to make it available to _extract_context
        new_metadata = list(handler_call_details.invocation_metadata)
        new_metadata.append(("x-user-id", str(user_id)))
        
        new_details = grpc.HandlerCallDetails(
            handler_call_details.method,
            tuple(new_metadata)
        )

        return await continuation(new_details)

    def _abort(self, code: grpc.StatusCode, details: str):
        """Returns a generic unary abort action."""
        async def abort_handler(request, context):
            await context.abort(code, details)
        return grpc.unary_unary_rpc_method_handler(abort_handler)
