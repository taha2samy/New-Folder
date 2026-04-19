"""Security and Context dependencies for FastAPI / Strawberry."""

import uuid
from fastapi import Request

def extract_metadata(request: Request):
    """
    Extracts the authorization header from the raw HTTP request into gRPC metadata tuple format.
    Generates an X-Correlation-ID for traceability downstream.
    Returns metadata tuple and the raw JWT token.
    """
    metadata = []
    raw_token = ""
    
    auth_header = request.headers.get("authorization")
    if auth_header:
        metadata.append(("authorization", auth_header))
        if auth_header.startswith("Bearer "):
            raw_token = auth_header[7:]
        else:
            raw_token = auth_header
            
    trace_id = request.headers.get("x-correlation-id", str(uuid.uuid4()))
    metadata.append(("x-trace-id", trace_id))

    return tuple(metadata), raw_token

class CustomContext:
    """Custom context object passed into every Strawberry resolver."""
    def __init__(self, metadata: tuple, token: str):
        self.metadata = metadata
        self.token = token

def get_context(request: Request) -> CustomContext:
    """FastAPI Dependency for Strawberry."""
    metadata, token = extract_metadata(request)
    return CustomContext(metadata=metadata, token=token)
