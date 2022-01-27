import pytest
from httpx import AsyncClient

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
