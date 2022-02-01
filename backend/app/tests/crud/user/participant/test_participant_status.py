import pytest
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.schemas import ParticipantStatusCreate, ParticipantStatusUpdate
from app.tests import utils_for_testing as ut

# This is the same as using the @pytest.mark.anyio on all test functions in the module
pytestmark = pytest.mark.anyio


async def test_create_participant_status(db_tests: AsyncSession) -> None:
    name = ut.random_lower_string(8)
    created_participant_status = await crud.participant_status.create(db_tests,
                                                                      obj_in=ParticipantStatusCreate(name=name))
    assert created_participant_status.name == name


async def test_get_participant_status(db_tests: AsyncSession) -> None:
    name = ut.random_lower_string(8)
    created_participant_status = await crud.participant_status.create(db_tests,
                                                                      obj_in=ParticipantStatusCreate(name=name))
    got_participant_status = await crud.participant_status.get(db_tests, id=created_participant_status.id)
    assert got_participant_status
    assert got_participant_status.name == name
    assert jsonable_encoder(created_participant_status) == jsonable_encoder(got_participant_status)


async def test_update_participant_status(db_tests: AsyncSession) -> None:
    created_participant_status = await crud.participant_status.create(
        db_tests,
        obj_in=ParticipantStatusCreate(name=ut.random_lower_string(8)))
    participant_status_in_update = ParticipantStatusUpdate(name=ut.random_lower_string(8))
    await crud.participant_status.update(db_tests, db_obj=created_participant_status,
                                         obj_in=participant_status_in_update)
    updated_participant_status = await crud.participant_status.get(db_tests, id=created_participant_status.id)
    assert updated_participant_status


async def test_remove_participant_status(db_tests: AsyncSession) -> None:
    created_participant_status = await crud.participant_status.create(
        db_tests,
        obj_in=ParticipantStatusCreate(name=ut.random_lower_string(8)))
    await crud.participant_status.remove(db_tests, id=created_participant_status.id)
    removed_participant_status = await crud.participant_status.get(db_tests, id=created_participant_status.id)
    assert removed_participant_status is None


async def test_get_by_name(db_tests: AsyncSession) -> None:
    db_p_status = await crud.participant_status.create(
        db_tests,
        obj_in=ParticipantStatusCreate(name=ut.random_lower_string(8)))

    assert (await crud.participant_status.get_by_name(db_tests, db_p_status.name)).id == db_p_status.id
    assert await crud.participant_status.get_by_name(db_tests, ut.random_lower_string(12)) is None
