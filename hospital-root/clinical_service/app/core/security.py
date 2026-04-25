"""Security utilities for JWT validation."""

import jwt
from typing import Dict, Any, Optional
from app.core.config import settings

def decode_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        decoded = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return decoded
    except jwt.PyJWTError:
        return None

def generate_internal_token() -> str:
    """Generates a short-lived JWT for inter-service communication."""
    payload = {
        "user_id": "clinical_service_internal",
        "role": "internal_service",
        "exp": jwt.datetime.utcnow() + jwt.timedelta(minutes=5)
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


