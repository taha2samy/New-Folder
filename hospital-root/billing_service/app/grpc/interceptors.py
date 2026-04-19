import grpc
from app.core.security import decode_token

class JWTInterceptor(grpc.aio.ServerInterceptor):
    def __init__(self):
        # Note: Unauthenticated endpoints or specific internal ones can be excluded here if needed.
        pass

    async def intercept_service(self, continuation, handler_call_details):
        metadata = dict(handler_call_details.invocation_metadata)
        
        token = metadata.get("authorization", "")
        if token.startswith("Bearer "):
            token = token[7:]
        else:
            token = metadata.get("x-jwt-token", "")
            
        if not token:
            return grpc.unary_unary_rpc_method_handler(
                lambda r, c: self._abort(c, grpc.StatusCode.UNAUTHENTICATED, "Missing token.")
            )

        payload = decode_token(token)
        if not payload:
            return grpc.unary_unary_rpc_method_handler(
                lambda r, c: self._abort(c, grpc.StatusCode.UNAUTHENTICATED, "Invalid token.")
            )

        # Inject payload into context if needed, but in standard Python gRPC we usually fetch again
        # or we just let it pass.
        return await continuation(handler_call_details)

    async def _abort(self, context, code, details):
        await context.abort(code, details)
