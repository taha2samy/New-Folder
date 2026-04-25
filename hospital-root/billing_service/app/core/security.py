import datetime
from jose import JWTError, jwt
from app.core.config import settings

def decode_token(token: str):
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None

def generate_internal_token():
    """Generates a short-lived internal service JWT."""
    payload = {
        "sub": "billing-service",
        "role": "internal_service",
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
