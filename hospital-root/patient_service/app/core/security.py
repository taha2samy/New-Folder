"""Security utilities for JWT validation."""

import jwt
from typing import Dict, Any, Optional
from app.core.config import settings

def decode_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodes and validates a JWT token.
    
    Args:
        token: The Bearer token string.
        
    Returns:
        The decoded dictionary payload if valid, None otherwise.
        Expected payload to contain 'sub' (user_id).
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

