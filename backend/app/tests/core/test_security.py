import datetime as dt

from jose import jwt

from app.core.config import settings
from app.core import security
from app.core.security import (
    create_access_token,
    verify_password,
    get_password_hash,
    generate_api_key_reset_token,
    verify_api_key_reset_token
)


def test_create_access_token_expires_delta_none() -> None:
    encoded_jwt = create_access_token("subject who need token")
    decoded_jwt = jwt.decode(encoded_jwt, settings.SECRET_KEY, algorithms=security.ALGORITHM)
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
    decoded_jwt = jwt.decode(encoded_jwt, settings.SECRET_KEY, algorithms=security.ALGORITHM)
    assert decoded_jwt['sub'] == "subject who need token"

    expected_expire_datetime = dt.datetime.utcnow() + expires_delta
    decoded_expire_datetime = dt.datetime.utcfromtimestamp(decoded_jwt['exp'])

    assert expected_expire_datetime.year == decoded_expire_datetime.year
    assert expected_expire_datetime.month == decoded_expire_datetime.month
    assert expected_expire_datetime.day == decoded_expire_datetime.day
    assert expected_expire_datetime.hour == decoded_expire_datetime.hour


def test_verify_password() -> None:
    plain_pwd = "my very secret pwd"
    hashed_pwd = security.pwd_context.hash(plain_pwd)
    assert verify_password(plain_pwd, hashed_pwd)
    assert not verify_password("wrong pwd", hashed_pwd)


def test_get_password_hash() -> None:
    plain_pwd = "my very secret pwd"
    hashed_pwd = get_password_hash(plain_pwd)
    assert security.pwd_context.verify(plain_pwd, hashed_pwd)
    assert not security.pwd_context.verify("wrong pwd", hashed_pwd)


def test_generate_api_key_reset_token() -> None:
    expected_expire_datetime = dt.datetime.utcnow() + dt.timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    encoded_jwt = generate_api_key_reset_token(settings.TESTS_EMAIL)

    decoded_jwt = jwt.decode(encoded_jwt, settings.SECRET_KEY, algorithms=security.ALGORITHM)
    decoded_expire_datetime = dt.datetime.fromtimestamp(decoded_jwt['exp'])

    assert expected_expire_datetime.year == decoded_expire_datetime.year
    assert expected_expire_datetime.month == decoded_expire_datetime.month
    assert expected_expire_datetime.day == decoded_expire_datetime.day
    assert expected_expire_datetime.hour == decoded_expire_datetime.hour


def test_verify_api_key_reset_token() -> None:
    encoded_jwt = jwt.encode(
        {
            "exp": (dt.datetime.utcnow() + dt.timedelta(hours=12)).timestamp(),
            "nbf": dt.datetime.utcnow(),
            "sub": settings.TESTS_EMAIL
        },
        settings.SECRET_KEY,
        algorithm=security.ALGORITHM)
    assert verify_api_key_reset_token(encoded_jwt) == settings.TESTS_EMAIL


def test_verify_api_key_reset_token_expiring_raises_JWTError(mocker) -> None:
    exp_yesterday = dt.datetime.utcnow() - dt.timedelta(days=1)
    mock_now = mocker.patch('app.core.security.dt.datetime')
    mock_now.utcnow.return_value = exp_yesterday
    expired_encoded_jwt = generate_api_key_reset_token(settings.TESTS_EMAIL)
    # tested function returns None when JWTError is raised :
    assert verify_api_key_reset_token(expired_encoded_jwt) is None
