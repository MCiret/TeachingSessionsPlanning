import datetime as dt
from typing import Any

from jose import jwt

from passlib.context import CryptContext

from app.core.config import settings
from app.core.security import create_access_token, verify_password, get_password_hash

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"  # algorithm used to sign the JWT token


def test_create_access_token_expires_delta_none() -> None:
    encoded_jwt = create_access_token("subject who need token")
    decoded_jwt = jwt.decode(encoded_jwt, settings.SECRET_KEY, algorithms=ALGORITHM)
    assert decoded_jwt['sub'] == "subject who need token"

    expected_expire_datetime = dt.datetime.utcnow() + dt.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    decoded_expire_datetime = dt.datetime.utcfromtimestamp(decoded_jwt['exp'])
    assert expected_expire_datetime.year == decoded_expire_datetime.year
    assert expected_expire_datetime.month == decoded_expire_datetime.month
    assert expected_expire_datetime.day == decoded_expire_datetime.day
    assert expected_expire_datetime.hour == decoded_expire_datetime.hour


def test_create_access_token_expires_delta_set() -> None:
    expires_delta = dt.timedelta(minutes=60)
    encoded_jwt = create_access_token("subject who need token", expires_delta=expires_delta)
    decoded_jwt = jwt.decode(encoded_jwt, settings.SECRET_KEY, algorithms=ALGORITHM)
    assert decoded_jwt['sub'] == "subject who need token"

    expected_expire_datetime = dt.datetime.utcnow() + expires_delta
    decoded_expire_datetime = dt.datetime.utcfromtimestamp(decoded_jwt['exp'])
    assert expected_expire_datetime.year == decoded_expire_datetime.year
    assert expected_expire_datetime.month == decoded_expire_datetime.month
    assert expected_expire_datetime.day == decoded_expire_datetime.day
    assert expected_expire_datetime.hour == decoded_expire_datetime.hour


def test_verify_password() -> None:
    plain_pwd = "my very secret pwd"
    hashed_pwd = pwd_context.hash(plain_pwd)
    assert verify_password(plain_pwd, hashed_pwd)
    assert not verify_password("wrong pwd", hashed_pwd)


def test_get_password_hash() -> None:
    plain_pwd = "my very secret pwd"
    hashed_pwd = get_password_hash(plain_pwd)
    assert pwd_context.verify(plain_pwd, hashed_pwd)
    assert not pwd_context.verify("wrong pwd", hashed_pwd)
