import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.encoders import jsonable_encoder

from app.core.config import settings
from app import crud
from app.schemas import SessionStatusCreate, SessionStatusUpdate
from app.tests import utils as ut

# This is the same as using the @pytest.mark.anyio on all test functions in the module
pytestmark = pytest.mark.anyio


async def test_read_session_status(async_client: AsyncClient, db_tests: AsyncSession,
                                  admin_token_headers: dict[str, str]) -> None:
    ss1 = await crud.session_status.create(db_tests, obj_in=SessionStatusCreate(name=ut.random_lower_string(10),
                                                                            nb_session_week=2))
    ss2 = await crud.session_status.create(db_tests, obj_in=SessionStatusCreate(name=ut.random_lower_string(10),
                                                                            nb_session_week=4))
    ss3 = await crud.session_status.create(db_tests, obj_in=SessionStatusCreate(name=ut.random_lower_string(10),
                                                                            nb_session_week=6))
    r = await async_client.get(f"{settings.API_V1_STR}/sessions/status", headers=admin_token_headers)
    r_status = r.json()
    assert len(r_status) >= 3
    ss_names = [ss["name"] for ss in r_status]
    assert (ss1.name and ss2.name and ss3.name in ss_names)
    await crud.session_status.remove(db_tests, id=ss1.id)
    await crud.session_status.remove(db_tests, id=ss2.id)
    await crud.session_status.remove(db_tests, id=ss3.id)


async def test_create_session_status(async_client: AsyncClient, db_tests: AsyncSession,
                                   admin_token_headers: dict[str, str]) -> None:
    name = ut.random_lower_string(10)
    data = jsonable_encoder(SessionStatusCreate(name=name))
    r = await async_client.post(f"{settings.API_V1_STR}/sessions/status",
                                headers=admin_token_headers, json=data)
    assert r.status_code == 200
    status = r.json()
    assert status["name"] == name
    assert (await crud.session_status.get(db_tests, id=status["id"])).name == name
    await crud.session_status.remove(db_tests, id=status["id"])


async def test_create_session_status_exisitng_name(async_client: AsyncClient, admin_token_headers: dict[str, str],
                                                   mocker) -> None:
    mock_get_by_name = mocker.patch('app.crud.session_status.get_by_name')
    mock_get_by_name.return_value = True
    name = ut.random_lower_string(10)
    data = jsonable_encoder(SessionStatusCreate(name=name))
    r = await async_client.post(f"{settings.API_V1_STR}/sessions/status",
                                headers=admin_token_headers, json=data)
    assert r.status_code == 400
    assert "A session status with this name already exists in the system..." in r.json().values()
    assert mock_get_by_name.called


async def test_update_session_status(async_client: AsyncClient, db_tests: AsyncSession,
                                   admin_token_headers: dict[str, str]) -> None:
    name = ut.random_lower_string(10)
    data = jsonable_encoder(SessionStatusCreate(name=name))
    r = await async_client.post(f"{settings.API_V1_STR}/sessions/status",
                                headers=admin_token_headers, json=data)
    assert r.status_code == 200
    status = r.json()
    assert status["name"] == name
    assert (await crud.session_status.get(db_tests, id=status["id"])).name == name
    await crud.session_status.remove(db_tests, id=status["id"])
