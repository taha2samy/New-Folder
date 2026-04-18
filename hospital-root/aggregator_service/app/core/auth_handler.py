"""Security and Context dependencies for FastAPI / Strawberry."""

import uuid
from fastapi import Request

def extract_metadata(request: Request) -> tuple:
    """
    Extracts the authorization header from the raw HTTP request into gRPC metadata tuple format.
    Generates an X-Correlation-ID for traceability downstream.
    """
    metadata = []
    auth_header = request.headers.get("authorization")
    if auth_header:
        metadata.append(("authorization", auth_header))
        
    trace_id = request.headers.get("x-correlation-id", str(uuid.uuid4()))
    metadata.append(("x-trace-id", trace_id))

    return tuple(metadata)

class CustomContext:
    """Custom context object passed into every Strawberry resolver."""
    def __init__(self, metadata: tuple):
        self.metadata = metadata

def get_context(request: Request) -> CustomContext:
    """FastAPI Dependency for Strawberry."""
    metadata = extract_metadata(request)
    return CustomContext(metadata=metadata)
