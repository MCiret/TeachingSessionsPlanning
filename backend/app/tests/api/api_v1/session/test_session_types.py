import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.encoders import jsonable_encoder

from app.core.config import settings
from app import crud
from app.schemas import SessionTypeCreate, SessionTypeUpdate
from app.tests import utils as ut

# This is the same as using the @pytest.mark.anyio on all test functions in the module
pytestmark = pytest.mark.anyio


async def test_read_session_types(async_client: AsyncClient, db_tests: AsyncSession,
                                  admin_token_headers: dict[str, str]) -> None:
    st1 = await crud.session_type.create(db_tests, obj_in=SessionTypeCreate(name=ut.random_lower_string(10),
                                                                            nb_session_week=2))
    st2 = await crud.session_type.create(db_tests, obj_in=SessionTypeCreate(name=ut.random_lower_string(10),
                                                                            nb_session_week=4))
    st3 = await crud.session_type.create(db_tests, obj_in=SessionTypeCreate(name=ut.random_lower_string(10),
                                                                            nb_session_week=6))
    r = await async_client.get(f"{settings.API_V1_STR}/sessions/types", headers=admin_token_headers)
    r_types = r.json()
    assert len(r_types) >= 3
    st_names = [st["name"] for st in r_types]
    assert (st1.name and st2.name and st3.name in st_names)
    await crud.session_type.remove(db_tests, id=st1.id)
    await crud.session_type.remove(db_tests, id=st2.id)
    await crud.session_type.remove(db_tests, id=st3.id)


async def test_create_session_type(async_client: AsyncClient, db_tests: AsyncSession,
                                   admin_token_headers: dict[str, str]) -> None:
    name = ut.random_lower_string(10)
    data = jsonable_encoder(SessionTypeCreate(name=name))
    r = await async_client.post(f"{settings.API_V1_STR}/sessions/type",
                                headers=admin_token_headers, json=data)
    assert r.status_code == 200
    type = r.json()
    assert type["name"] == name
    assert (await crud.session_type.get(db_tests, id=type["id"])).name == name
    await crud.session_type.remove(db_tests, id=type["id"])


async def test_create_session_type_exisitng_name(async_client: AsyncClient, admin_token_headers: dict[str, str],
                                                 mocker) -> None:
    mock_get_by_name = mocker.patch('app.crud.session_type.get_by_name')
    mock_get_by_name.return_value = True
    name = ut.random_lower_string(10)
    data = jsonable_encoder(SessionTypeCreate(name=name))
    r = await async_client.post(f"{settings.API_V1_STR}/sessions/type",
                                headers=admin_token_headers, json=data)
    assert r.status_code == 400
    assert "A session type with this name already exists in the system..." in r.json().values()
    assert mock_get_by_name.called


async def test_update_session_type(async_client: AsyncClient, db_tests: AsyncSession,
                                   admin_token_headers: dict[str, str]) -> None:
    name = ut.random_lower_string(10)
    data = jsonable_encoder(SessionTypeCreate(name=name))
    r = await async_client.post(f"{settings.API_V1_STR}/sessions/type",
                                headers=admin_token_headers, json=data)
    assert r.status_code == 200
    type = r.json()
    assert type["name"] == name
    assert (await crud.session_type.get(db_tests, id=type["id"])).name == name
    await crud.session_type.remove(db_tests, id=type["id"])
