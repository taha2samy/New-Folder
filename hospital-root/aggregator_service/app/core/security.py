"""Security utilities for the Aggregator Service."""

import jwt
import datetime
from typing import Optional, Dict, Any
from app.core.config import settings

def generate_jwt_token(user_id: str, role: str, expiration_minutes: int = 60) -> str:
    """
    Generates a signed JWT token for service-to-service or test communication.
    """
    payload = {
        "sub": user_id,
        "role": role,
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=expiration_minutes)
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodes and validates a JWT token using the shared secret.
    """
    try:
        decoded = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return decoded
    except jwt.PyJWTError:
        return None