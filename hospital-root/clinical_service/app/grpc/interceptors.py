"""gRPC interceptors for clinical_service."""

import grpc
from typing import Callable, Any
from app.core.security import decode_jwt_token
from app.core.config import settings

class AuthInterceptor(grpc.aio.ServerInterceptor):
    async def intercept_service(self, continuation: Callable, handler_call_details: grpc.HandlerCallDetails) -> Any:
        metadata = dict(handler_call_details.invocation_metadata)
        auth_header = metadata.get("authorization")
        internal_secret = metadata.get("x-internal-secret")

        user_id = None
        token = None

        # 1. Check Internal Secret
        if internal_secret == settings.INTERNAL_API_SECRET:
            user_id = "system-internal"
            token = "internal-bypass"
        
        # 2. Check JWT Token
        elif auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            decoded = decode_jwt_token(token)
            if decoded:
                user_id = decoded.get("sub")

        if not user_id:
            return self._abort(grpc.StatusCode.UNAUTHENTICATED, "Authentication failed.")
            
        new_metadata = list(handler_call_details.invocation_metadata)
        new_metadata.append(("x-user-id", str(user_id)))
        new_metadata.append(("x-jwt-token", str(token)))
        
        new_details = grpc.HandlerCallDetails(
            handler_call_details.method,
            tuple(new_metadata)
        )

        return await continuation(new_details)

    def _abort(self, code: grpc.StatusCode, details: str):
        async def abort_handler(request, context):
            await context.abort(code, details)
        return grpc.unary_unary_rpc_method_handler(abort_handler)
