import pytest
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.schemas.session.session_status import SessionStatusCreate, SessionStatusUpdate
from app.tests import utils_for_testing as ut

# This is the same as using the @pytest.mark.anyio on all test functions in the module
pytestmark = pytest.mark.anyio


async def test_create_session_status(db_tests: AsyncSession) -> None:
    name = ut.random_lower_string(8)
    created_session_status = await crud.session_status.create(db_tests, obj_in=SessionStatusCreate(name=name))
    assert created_session_status.name == name


async def test_get_session_status(db_tests: AsyncSession) -> None:
    name = ut.random_lower_string(8)
    created_session_status = await crud.session_status.create(db_tests, obj_in=SessionStatusCreate(name=name))
    got_session_status = await crud.session_status.get(db_tests, id=created_session_status.id)
    assert got_session_status
    assert got_session_status.name == name
    assert jsonable_encoder(created_session_status) == jsonable_encoder(got_session_status)


async def test_update_session_status(db_tests: AsyncSession) -> None:
    created_session_status = await crud.session_status.create(
        db_tests,
        obj_in=SessionStatusCreate(name=ut.random_lower_string(8)))
    session_status_in_update = SessionStatusUpdate(name=ut.random_lower_string(8))
    await crud.session_status.update(db_tests, db_obj=created_session_status, obj_in=session_status_in_update)
    updated_session_status = await crud.session_status.get(db_tests, id=created_session_status.id)
    assert updated_session_status
    assert updated_session_status.name == session_status_in_update.name
    assert created_session_status.id == updated_session_status.id


async def test_remove_session_status(db_tests: AsyncSession) -> None:
    created_session_status = await crud.session_status.create(
        db_tests,
        obj_in=SessionStatusCreate(name=ut.random_lower_string(8)))
    await crud.session_status.remove(db_tests, id=created_session_status.id)
    removed_session_status = await crud.session_status.get(db_tests, id=created_session_status.id)
    assert removed_session_status is None


async def test_get_by_name(db_tests: AsyncSession) -> None:
    db_s_status = await crud.session_status.create(
        db_tests,
        obj_in=SessionStatusCreate(name=ut.random_lower_string(8)))

    assert (await crud.session_status.get_by_name(db_tests, name=db_s_status.name)).id == db_s_status.id
    assert await crud.session_status.get_by_name(db_tests, name=ut.random_lower_string(12)) is None
