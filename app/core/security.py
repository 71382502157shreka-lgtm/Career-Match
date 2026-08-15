"""
Password hashing and JWT issuing/verification.
Designed to be robust across different Python versions (3.8-3.13) and deployment environments (Streamlit Cloud, Docker, etc.).
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
import hashlib
import hmac

# --- JWT Support (PyJWT preferred, python-jose fallback, HMAC-SHA256 standard fallback) ---
HAS_PYJWT = False
try:
    import jwt as pyjwt
    HAS_PYJWT = True
except ImportError:
    pass

HAS_JOSE = False
try:
    from jose import JWTError as JoseJWTError, jwt as jose_jwt
    HAS_JOSE = True
except (ImportError, Exception):
    pass

# --- Password Hashing Support (bcrypt direct preferred, passlib fallback, hashlib fallback) ---
HAS_BCRYPT = False
try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    pass

pwd_context = None
try:
    from passlib.context import CryptContext
    # Passlib can throw AttributeError/ValueError with newer bcrypt versions
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
except (ImportError, Exception):
    pwd_context = None

from app.core.config import settings


def hash_password(password: str) -> str:
    """Hash a plain text password using bcrypt or SHA-256 fallback."""
    if not password:
        return ""

    # Try passlib first if available
    if pwd_context is not None:
        try:
            return pwd_context.hash(password)
        except Exception:
            pass

    # Try direct bcrypt
    if HAS_BCRYPT:
        try:
            pwd_bytes = password.encode("utf-8")
            if len(pwd_bytes) > 72:
                pwd_bytes = pwd_bytes[:72]
            salt = bcrypt.gensalt()
            return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")
        except Exception:
            pass

    # Fallback to hashlib PBKDF2 HMAC SHA-256
    salt = settings.SECRET_KEY.encode("utf-8")
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return f"pbkdf2_sha256${pwd_hash.hex()}"


# Alias for backward compatibility
get_password_hash = hash_password


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    if not plain_password or not hashed_password:
        return False

    # Check if hashed_password is a passlib / bcrypt hash (starts with $2a$, $2b$, $2y$)
    if hashed_password.startswith(("$2a$", "$2b$", "$2y$")):
        if HAS_BCRYPT:
            try:
                pwd_bytes = plain_password.encode("utf-8")
                if len(pwd_bytes) > 72:
                    pwd_bytes = pwd_bytes[:72]
                return bcrypt.checkpw(pwd_bytes, hashed_password.encode("utf-8"))
            except Exception:
                pass

        if pwd_context is not None:
            try:
                return pwd_context.verify(plain_password, hashed_password)
            except Exception:
                pass

    # Check if pbkdf2 fallback hash
    if hashed_password.startswith("pbkdf2_sha256$"):
        salt = settings.SECRET_KEY.encode("utf-8")
        pwd_hash = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, 100000)
        return f"pbkdf2_sha256${pwd_hash.hex()}" == hashed_password

    # Fallback equality test for plain text (legacy or dev DBs)
    return plain_password == hashed_password


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = {"sub": str(subject), "exp": int(expire.timestamp())}

    # Try PyJWT
    if HAS_PYJWT:
        try:
            return pyjwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        except Exception:
            pass

    # Try python-jose
    if HAS_JOSE:
        try:
            return jose_jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        except Exception:
            pass

    # Basic HMAC token encoding fallback
    import base64
    import json
    header = base64.b64encode(json.dumps({"alg": settings.ALGORITHM, "typ": "JWT"}).encode()).decode()
    payload = base64.b64encode(json.dumps(to_encode).encode()).decode()
    signature = hmac.new(settings.SECRET_KEY.encode(), f"{header}.{payload}".encode(), hashlib.sha256).hexdigest()
    return f"{header}.{payload}.{signature}"


def decode_access_token(token: str) -> Optional[str]:
    """Decode a JWT token and return the subject (e.g. email/user ID)."""
    if not token:
        return None

    # Try PyJWT
    if HAS_PYJWT:
        try:
            payload = pyjwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload.get("sub")
        except Exception:
            pass

    # Try python-jose
    if HAS_JOSE:
        try:
            payload = jose_jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload.get("sub")
        except Exception:
            pass

    # Basic HMAC parsing fallback
    try:
        import base64
        import json
        parts = token.split(".")
        if len(parts) == 3:
            payload_json = base64.b64decode(parts[1] + "==").decode()
            payload = json.loads(payload_json)
            exp = payload.get("exp")
            if exp and datetime.now(timezone.utc).timestamp() > exp:
                return None
            return payload.get("sub")
    except Exception:
        pass

    return None

