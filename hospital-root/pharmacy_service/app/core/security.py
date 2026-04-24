"""Security utilities for JWT validation in pharmacy_service."""

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


