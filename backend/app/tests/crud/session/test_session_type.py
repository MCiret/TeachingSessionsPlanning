import pytest
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.schemas.session.session_type import SessionTypeCreate, SessionTypeUpdate
from app.tests import utils as ut

# This is the same as using the @pytest.mark.anyio on all test functions in the module
pytestmark = pytest.mark.anyio


async def test_create_session_type(db_tests: AsyncSession) -> None:
    name = ut.random_lower_string(8)
    created_session_type = await crud.session_type.create(db_tests, obj_in=SessionTypeCreate(name=name))
    assert created_session_type.name == name


async def test_get_session_type(db_tests: AsyncSession) -> None:
    name = ut.random_lower_string(8)
    created_session_type = await crud.session_type.create(db_tests, obj_in=SessionTypeCreate(name=name))
    got_session_type = await crud.session_type.get(db_tests, id=created_session_type.id)
    assert got_session_type
    assert got_session_type.name == name
    assert jsonable_encoder(created_session_type) == jsonable_encoder(got_session_type)


async def test_update_session_type(db_tests: AsyncSession) -> None:
    created_session_type = await crud.session_type.create(db_tests,
                                                          obj_in=SessionTypeCreate(name=ut.random_lower_string(8)))
    session_type_in_update = SessionTypeUpdate(name=ut.random_lower_string(8))
    await crud.session_type.update(db_tests, db_obj=created_session_type, obj_in=session_type_in_update)
    updated_session_type = await crud.session_type.get(db_tests, id=created_session_type.id)
    assert updated_session_type
    assert updated_session_type.name == session_type_in_update.name
    assert created_session_type.id == updated_session_type.id


async def test_remove_session_type(db_tests: AsyncSession) -> None:
    created_session_type = await crud.session_type.create(db_tests,
                                                          obj_in=SessionTypeCreate(name=ut.random_lower_string(8)))
    await crud.session_type.remove(db_tests, id=created_session_type.id)
    removed_session_type = await crud.session_type.get(db_tests, id=created_session_type.id)
    assert removed_session_type is None


async def test_get_by_name(db_tests: AsyncSession) -> None:
    db_s_type = await crud.session_type.create(
        db_tests,
        obj_in=SessionTypeCreate(name=ut.random_lower_string(8)))

    assert (await crud.session_type.get_by_name(db_tests, name=db_s_type.name)).id == db_s_type.id
    assert await crud.session_type.get_by_name(db_tests, name=ut.random_lower_string(12)) is None
