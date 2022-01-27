import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.encoders import jsonable_encoder

from app.core.config import settings
from app import crud
from app.schemas import ParticipantStatusCreate, ParticipantStatusUpdate
from app.tests import utils as ut

# This is the same as using the @pytest.mark.anyio on all test functions in the module
pytestmark = pytest.mark.anyio


async def test_read_participant_statuss_by_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                                 admin_token_headers: dict[str, str]) -> None:
    await crud.participant_status.create(db_tests, obj_in=ParticipantStatusCreate(name=ut.random_lower_string(10)))
    await crud.participant_status.create(db_tests, obj_in=ParticipantStatusCreate(name=ut.random_lower_string(10)))
    await crud.participant_status.create(db_tests, obj_in=ParticipantStatusCreate(name=ut.random_lower_string(10)))
    r = await async_client.get(f"{settings.API_V1_STR}/users/participants/status", headers=admin_token_headers)
    r_status = r.json()
    assert len(r_status) >= 3
    for status in r_status:
        assert "name" in status


async def test_read_participant_status_by_not_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                                    speaker_token_headers: dict[str, str]) -> None:
    await crud.participant_status.create(db_tests, obj_in=ParticipantStatusCreate(name=ut.random_lower_string(10)))
    r = await async_client.get(f"{settings.API_V1_STR}/users/participants/status", headers=speaker_token_headers)
    assert r.status_code == 400
    assert "The user doesn't have enough privileges" in r.json().values()


async def test_create_participant_status_by_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                                  admin_token_headers: dict[str, str]) -> None:
    name = ut.random_lower_string(10)
    data = jsonable_encoder(ParticipantStatusCreate(name=name))
    r = await async_client.post(f"{settings.API_V1_STR}/users/participants/status",
                                headers=admin_token_headers, json=data)
    assert r.status_code == 200
    status = r.json()
    assert status["name"] == name
    assert (await crud.participant_status.get(db_tests, id=status["id"])).name == name


async def test_create_participant_status_by_not_admin(async_client: AsyncClient,
                                                      speaker_token_headers: dict[str, str]) -> None:
    name = ut.random_lower_string(10)
    data = jsonable_encoder(ParticipantStatusCreate(name=name))
    r = await async_client.post(f"{settings.API_V1_STR}/users/participants/status",
                                headers=speaker_token_headers, json=data)
    assert r.status_code == 400
    assert "The user doesn't have enough privileges" in r.json().values()


async def test_create_participant_status_existing_name_by_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                                                admin_token_headers: dict[str, str]) -> None:
    name = ut.random_lower_string(10)
    await crud.participant_status.create(db_tests, obj_in=ParticipantStatusCreate(name=name))
    data = jsonable_encoder(ParticipantStatusCreate(name=name))
    r = await async_client.post(f"{settings.API_V1_STR}/users/participants/status",
                                headers=admin_token_headers, json=data)
    assert r.status_code == 400
    assert "A participant status with this name already exists in the system..." in r.json().values()


async def test_update_participant_status_by_id_by_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                                        admin_token_headers: dict[str, str]) -> None:
    p_status = await crud.participant_status.create(db_tests,
                                                    obj_in=ParticipantStatusCreate(name=ut.random_lower_string(10)))
    data = jsonable_encoder(ParticipantStatusUpdate(name=ut.random_lower_string(10)))
    r = await async_client.put(f"{settings.API_V1_STR}/users/participants/status/{p_status.id}",
                               headers=admin_token_headers, json=data)
    assert r.status_code == 200
    assert r.json()["name"] != p_status.name


async def test_update_participant_status_by_id_by_not_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                                            speaker_token_headers: dict[str, str]) -> None:
    p_status = await crud.participant_status.create(db_tests,
                                                    obj_in=ParticipantStatusCreate(name=ut.random_lower_string(10)))
    data = jsonable_encoder(ParticipantStatusUpdate(), exclude_unset=True)
    r = await async_client.put(f"{settings.API_V1_STR}/users/participants/status/{p_status.id}",
                               headers=speaker_token_headers, json=data)
    assert r.status_code == 400
    assert "The user doesn't have enough privileges" in r.json().values()


async def test_update_participant_status_by_id_not_existing_by_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                                                     admin_token_headers: dict[str, str]) -> None:
    # get a not existing participant status id
    p_status = await crud.participant_status.get_multi(db_tests)
    if p_status:
        max_id = max([status.id for status in p_status])
    else:
        max_id = 0
    data = jsonable_encoder(ParticipantStatusUpdate(name=ut.random_lower_string(10)), exclude_unset=True)
    r = await async_client.put(f"{settings.API_V1_STR}/users/participants/status/{max_id + 1}",
                               headers=admin_token_headers, json=data)
    assert r.status_code == 404
    assert "A participant status with this id does not exist in the system..." in r.json().values()


async def test_update_participant_status_by_id_existing_name_by_admin(async_client: AsyncClient,
                                                                      db_tests: AsyncSession,
                                                                      admin_token_headers: dict[str, str]) -> None:
    p_status = await crud.participant_status.create(db_tests,
                                                    obj_in=ParticipantStatusCreate(name=ut.random_lower_string(10)))
    data = jsonable_encoder(ParticipantStatusUpdate(name=p_status.name), exclude_unset=True)
    r = await async_client.put(f"{settings.API_V1_STR}/users/participants/status/{p_status.id}",
                               headers=admin_token_headers, json=data)
    assert r.status_code == 400
    assert "A participant status with this name already exists in the system..." in r.json().values()
