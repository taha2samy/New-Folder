"""Security utilities: JWT decoding for master_data_service."""

from typing import Any, Dict, Optional

import jwt

from app.core.config import settings


def decode_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT bearer token.

    Returns the decoded claims dictionary on success, or None when the token
    is absent, malformed, expired, or carries an invalid signature.
    """
    try:
        decoded = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return decoded
    except jwt.PyJWTError:
        return None
