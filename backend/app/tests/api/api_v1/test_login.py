import pytest
from httpx import AsyncClient

from sqlalchemy.ext.asyncio import AsyncSession
from app.tests import utils_for_testing as ut
from app import crud
from app.core import security
from app.core.config import settings

# This is the same as using the @pytest.mark.anyio on all test functions in the module
pytestmark = pytest.mark.anyio

# this admin user is in db due to the init_data_tests_db autouse fixture (see conftest.py)
login_data = {
        "username": settings.FIRST_SUPERUSER_EMAIL,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }


async def test_login_access_token(async_client: AsyncClient) -> None:
    r = await async_client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    assert r.status_code == 200
    assert "access_token" in tokens
    assert "bearer" in tokens.values()
    assert tokens["access_token"]


async def test_login_access_token_if_user_not_authenticated(async_client: AsyncClient, mocker) -> None:
    mock_crud_user_authenticate = mocker.patch('app.crud.user.authenticate')
    mock_crud_user_authenticate.return_value = False
    r = await async_client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    assert r.status_code == 400
    assert "Incorrect email or api_key" in tokens.values()


async def test_login_access_token_if_user_not_active(async_client: AsyncClient, mocker) -> None:
    mock_crud_user_is_active = mocker.patch('app.crud.user.is_active')
    mock_crud_user_is_active.return_value = False
    r = await async_client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    assert r.status_code == 400
    assert "Inactive user" in tokens.values()


async def test_test_token_OK(async_client: AsyncClient, admin_token_headers: dict[str, str]) -> None:
    r = await async_client.post(
        f"{settings.API_V1_STR}/login/test-token", headers=admin_token_headers,
    )
    result = r.json()
    assert r.status_code == 200
    assert "email" in result


async def test_test_token_wrong_token(async_client: AsyncClient) -> None:
    admin_token_headers = {"Authorization": "Bearer mywro.ngtok.en"}
    r = await async_client.post(
        f"{settings.API_V1_STR}/login/test-token", headers=admin_token_headers,
    )
    assert r.status_code == 403


async def test_test_token_no_authorization_header(async_client: AsyncClient) -> None:
    admin_token_headers = {"Not": "Bearer mywro.ngtok.en"}
    r = await async_client.post(
        f"{settings.API_V1_STR}/login/test-token", headers=admin_token_headers,
    )
    assert r.status_code == 401


async def test_recover_api_key(db_tests: AsyncSession, async_client: AsyncClient) -> None:
    user = await ut.create_random_participant(db_tests)
    r = await async_client.post(
        f"{settings.API_V1_STR}/login/recover-api-key/{user.email}")
    assert r.status_code == 200
    assert {"msg": "Password recovery email sent"} == r.json()


async def test_recover_api_key_not_existing_user(async_client: AsyncClient) -> None:
    r = await async_client.post(
        f"{settings.API_V1_STR}/login/recover-api-key/not_existing_email@gmail.com")
    assert r.status_code == 404
    assert "The user with this username does not exist in the system..." in r.json().values()


async def test_reset_api_key_form(async_client: AsyncClient) -> None:
    r = await async_client.get(
        f"{settings.API_V1_STR}/login/reset-api-key-form?email={settings.TESTS_EMAIL}&token=jwttoken")
    assert r.status_code == 200
    assert (settings.TESTS_EMAIL
            and "Paste your new API Key :"
            and "jwttoken") in r.content.decode('utf-8')


@pytest.fixture
async def mocks_for_reset_api_key_tests(request, mocker):
    mock_verif_token = mocker.patch('app.core.security.verify_api_key_reset_token')
    mock_verif_token.return_value = request.node.get_closest_marker("verif_token").args[0]

    mock_get_by_email = mocker.patch('app.crud.user.get_by_email')
    mock_get_by_email.return_value = request.node.get_closest_marker("get_by_email").args[0]

    mock_is_active = mocker.patch('app.crud.user.is_active')
    mock_is_active.return_value = request.node.get_closest_marker("is_active").args[0]

    return mock_verif_token, mock_get_by_email, mock_is_active


async def test_reset_api_key(db_tests: AsyncSession, async_client: AsyncClient) -> None:
    user = await ut.create_random_participant(db_tests)
    ex_hashed_api_key = user.hashed_api_key
    form_data = {
        "new_api_key": "mysupersecret__new__api_key",
        "apikey_reset_token": security.generate_api_key_reset_token(user.email)
    }
    r = await async_client.post(
        f"{settings.API_V1_STR}/login/reset-api-key/", data=form_data)
    assert r.status_code == 200
    assert {"msg": "Password updated successfully"} == r.json()

    await db_tests.close()  # to update the user object (from db) in session
    db_user = await crud.user.get(db_tests, id=user.id)
    assert db_user.email == user.email
    assert db_user.hashed_api_key != ex_hashed_api_key
    assert security.verify_password(form_data["new_api_key"], db_user.hashed_api_key)

form_data = {
        "new_api_key": "mysupersecret__new__api_key",
        "apikey_reset_token": "encoded_apikey_reset_jwt_token"
    }


@pytest.mark.is_active(True)
@pytest.mark.get_by_email(True)
@pytest.mark.verif_token(False)
async def test_reset_api_key_invalid_token(async_client: AsyncClient, mocks_for_reset_api_key_tests) -> None:
    r = await async_client.post(
        f"{settings.API_V1_STR}/login/reset-api-key/", data=form_data)
    assert r.status_code == 400
    assert "Invalid token" in r.json().values()


@pytest.mark.is_active(True)
@pytest.mark.get_by_email(False)
@pytest.mark.verif_token(True)
async def test_reset_api_key_not_existing_email(async_client: AsyncClient, mocks_for_reset_api_key_tests) -> None:
    r = await async_client.post(
        f"{settings.API_V1_STR}/login/reset-api-key/", data=form_data)
    assert r.status_code == 404
    assert "The user with this username does not exist in the system..." in r.json().values()


@pytest.mark.is_active(False)
@pytest.mark.get_by_email(True)
@pytest.mark.verif_token(True)
async def test_reset_api_key_inactive_user(async_client: AsyncClient, mocks_for_reset_api_key_tests) -> None:
    r = await async_client.post(
        f"{settings.API_V1_STR}/login/reset-api-key/", data=form_data)
    assert r.status_code == 400
    assert "Inactive user" in r.json().values()
