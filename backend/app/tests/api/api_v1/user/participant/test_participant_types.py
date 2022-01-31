import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.encoders import jsonable_encoder

from app.core.config import settings
from app import crud
from app.schemas import ParticipantTypeCreate, ParticipantTypeUpdate
from app.tests import utils as ut

# This is the same as using the @pytest.mark.anyio on all test functions in the module
pytestmark = pytest.mark.anyio


async def test_read_participant_types_by_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                               admin_token_headers: dict[str, str]) -> None:
    await crud.participant_type.create(db_tests, obj_in=ParticipantTypeCreate(name=ut.random_lower_string(10),
                                                                              nb_session_week=2))
    await crud.participant_type.create(db_tests, obj_in=ParticipantTypeCreate(name=ut.random_lower_string(10),
                                                                              nb_session_week=4))
    await crud.participant_type.create(db_tests, obj_in=ParticipantTypeCreate(name=ut.random_lower_string(10),
                                                                              nb_session_week=6))
    r = await async_client.get(f"{settings.API_V1_STR}/users/participants/types", headers=admin_token_headers)
    r_types = r.json()
    assert len(r_types) >= 3
    for type in r_types:
        assert "name" in type
        assert "nb_session_week" in type


async def test_read_participant_types_by_not_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                                   speaker_token_headers: dict[str, str]) -> None:
    """Unnecessary test that actually tests the Depends() which is already tested in test_deps.py."""
    await crud.participant_type.create(db_tests, obj_in=ParticipantTypeCreate(name=ut.random_lower_string(10),
                                                                              nb_session_week=2))
    r = await async_client.get(f"{settings.API_V1_STR}/users/participants/types", headers=speaker_token_headers)
    assert r.status_code == 400
    assert "The user doesn't have enough privileges" in r.json().values()


async def test_create_participant_type_by_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                                admin_token_headers: dict[str, str]) -> None:
    name = ut.random_lower_string(10)
    data = jsonable_encoder(ParticipantTypeCreate(name=name, nb_session_week=2))
    r = await async_client.post(f"{settings.API_V1_STR}/users/participants/type",
                                headers=admin_token_headers, json=data)
    assert r.status_code == 200
    type = r.json()
    assert type["name"] == name
    assert (await crud.participant_type.get(db_tests, id=type["id"])).name == name


async def test_create_participant_type_by_not_admin(async_client: AsyncClient,
                                                    speaker_token_headers: dict[str, str]) -> None:
    """Unnecessary test that actually tests the Depends() which is already tested in test_deps.py."""
    name = ut.random_lower_string(10)
    data = jsonable_encoder(ParticipantTypeCreate(name=name, nb_session_week=2))
    r = await async_client.post(f"{settings.API_V1_STR}/users/participants/type",
                                headers=speaker_token_headers, json=data)
    assert r.status_code == 400
    assert "The user doesn't have enough privileges" in r.json().values()


async def test_create_participant_type_existing_name_by_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                                              admin_token_headers: dict[str, str]) -> None:
    name = ut.random_lower_string(10)
    await crud.participant_type.create(db_tests, obj_in=ParticipantTypeCreate(name=name, nb_session_week=2))
    data = jsonable_encoder(ParticipantTypeCreate(name=name, nb_session_week=2))
    r = await async_client.post(f"{settings.API_V1_STR}/users/participants/type",
                                headers=admin_token_headers, json=data)
    assert r.status_code == 400
    assert "A participant type with this name already exists in the system..." in r.json().values()


async def test_update_participant_type_by_id_by_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                                      admin_token_headers: dict[str, str]) -> None:
    p_type = await crud.participant_type.create(db_tests, obj_in=ParticipantTypeCreate(name=ut.random_lower_string(10),
                                                                                       nb_session_week=2))
    data = jsonable_encoder(ParticipantTypeUpdate(name=ut.random_lower_string(10),
                                                  nb_session_week=p_type.nb_session_week + 1))
    r = await async_client.put(f"{settings.API_V1_STR}/users/participants/type/{p_type.id}",
                               headers=admin_token_headers, json=data)
    assert r.status_code == 200
    assert r.json()["nb_session_week"] == p_type.nb_session_week + 1


async def test_update_participant_type_by_id_by_not_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                                          speaker_token_headers: dict[str, str]) -> None:
    """Unnecessary test that actually tests the Depends() which is already tested in test_deps.py."""
    p_type = await crud.participant_type.create(db_tests, obj_in=ParticipantTypeCreate(name=ut.random_lower_string(10),
                                                                                       nb_session_week=2))
    data = jsonable_encoder(ParticipantTypeUpdate(nb_session_week=p_type.nb_session_week + 1), exclude_unset=True)
    r = await async_client.put(f"{settings.API_V1_STR}/users/participants/type/{p_type.id}",
                               headers=speaker_token_headers, json=data)
    assert r.status_code == 400
    assert "The user doesn't have enough privileges" in r.json().values()


async def test_update_participant_type_by_id_not_existing_by_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                                                   admin_token_headers: dict[str, str]) -> None:
    # get a not existing participant type id
    p_types = await crud.participant_type.get_multi(db_tests)
    if p_types:
        max_id = max([type.id for type in p_types])
    else:
        max_id = 0
    data = jsonable_encoder(ParticipantTypeUpdate(name=ut.random_lower_string(10)), exclude_unset=True)
    r = await async_client.put(f"{settings.API_V1_STR}/users/participants/type/{max_id + 1}",
                               headers=admin_token_headers, json=data)
    assert r.status_code == 404
    assert "A participant type with this id does not exist in the system..." in r.json().values()


async def test_update_participant_type_by_id_existing_name_by_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                                                    admin_token_headers: dict[str, str]) -> None:
    p_type = await crud.participant_type.create(db_tests, obj_in=ParticipantTypeCreate(name=ut.random_lower_string(10),
                                                                                       nb_session_week=2))
    data = jsonable_encoder(ParticipantTypeUpdate(name=p_type.name), exclude_unset=True)
    r = await async_client.put(f"{settings.API_V1_STR}/users/participants/type/{p_type.id}",
                               headers=admin_token_headers, json=data)
    assert r.status_code == 400
    assert "A participant type with this name already exists in the system..." in r.json().values()
