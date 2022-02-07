import datetime as dt
from typing import Any

from jose import jwt

from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"  # algorithm used to sign the JWT token


def create_access_token(subject: str | Any, expires_delta: dt.timedelta = None) -> str:
    if expires_delta:
        expire = dt.datetime.utcnow() + expires_delta
    else:
        expire = dt.datetime.utcnow() + dt.timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(claims=to_encode, key=settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def generate_api_key_reset_token(email: str) -> str:
    delta = dt.timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    now = dt.datetime.utcnow()
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode({"exp": exp, "nbf": now, "sub": email}, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_api_key_reset_token(token: str) -> str | None:
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=ALGORITHM)
        return decoded_token["sub"]
    except jwt.JWTError:
        return None
