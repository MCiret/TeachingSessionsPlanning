import pytest
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.schemas import ParticipantTypeCreate, ParticipantTypeUpdate
from app.tests import utils as ut

# This is the same as using the @pytest.mark.anyio on all test functions in the module
pytestmark = pytest.mark.anyio


async def test_create_participant_type(db_tests: AsyncSession) -> None:
    name = ut.random_lower_string(8)
    created_participant_type = await crud.participant_type.create(
        db_tests,
        obj_in=ParticipantTypeCreate(name=name, nb_session_week=3))
    assert created_participant_type.name == name
    assert hasattr(created_participant_type, "nb_session_week")


async def test_get_participant_type(db_tests: AsyncSession) -> None:
    name = ut.random_lower_string(8)
    created_participant_type = await crud.participant_type.create(
        db_tests,
        obj_in=ParticipantTypeCreate(name=name, nb_session_week=3))
    got_participant_type = await crud.participant_type.get(db_tests, id=created_participant_type.id)
    assert got_participant_type
    assert got_participant_type.name == name
    assert jsonable_encoder(created_participant_type) == jsonable_encoder(got_participant_type)


async def test_update_participant_type(db_tests: AsyncSession) -> None:
    created_participant_type = await crud.participant_type.create(
        db_tests, obj_in=ParticipantTypeCreate(name=ut.random_lower_string(8), nb_session_week=3))
    participant_type_in_update = ParticipantTypeUpdate(nb_session_week=4)
    await crud.participant_type.update(db_tests, db_obj=created_participant_type, obj_in=participant_type_in_update)
    updated_participant_type = await crud.participant_type.get(db_tests, id=created_participant_type.id)
    assert updated_participant_type
    assert created_participant_type.nb_session_week == 4


async def test_remove_participant_type(db_tests: AsyncSession) -> None:
    created_participant_type = await crud.participant_type.create(
        db_tests,
        obj_in=ParticipantTypeCreate(name=ut.random_lower_string(8), nb_session_week=3))
    await crud.participant_type.remove(db_tests, id=created_participant_type.id)
    removed_participant_type = await crud.participant_type.get(db_tests, id=created_participant_type.id)
    assert removed_participant_type is None


async def test_get_max_nb_session_week(db_tests: AsyncSession) -> None:
    db_p_types = await crud.participant_type.get_multi(db_tests, limit=None)
    nb_session_week_list = [p_type.nb_session_week for p_type in db_p_types]
    max_nb_session_week = max(nb_session_week_list)

    assert await crud.participant_type.get_max_nb_session_week(db_tests) == max_nb_session_week
