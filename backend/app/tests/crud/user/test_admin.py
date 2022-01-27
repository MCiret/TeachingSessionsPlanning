import pytest
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.schemas import AdminUpdate
from app.core.security import verify_password
from app.tests import utils as ut

# This is the same as using the @pytest.mark.anyio on all test functions in the module
pytestmark = pytest.mark.anyio


async def test_create_admin(db_tests: AsyncSession) -> None:
    email = ut.random_email()
    created_admin = await ut.create_random_admin(db_tests, email=email)
    assert created_admin.email == email
    assert created_admin.profile == "admin"
    assert hasattr(created_admin, "hashed_api_key")


async def test_get_admin(db_tests: AsyncSession) -> None:
    created_admin = await ut.create_random_admin(db_tests)
    got_admin = await crud.admin.get(db_tests, id=created_admin.id)
    assert got_admin
    assert got_admin.profile == "admin"
    assert created_admin.email == got_admin.email
    assert jsonable_encoder(created_admin) == jsonable_encoder(got_admin)


async def test_update_admin_using_pydantic_schema(db_tests: AsyncSession) -> None:
    created_admin = await ut.create_random_admin(db_tests)
    new_api_key = ut.random_lower_string(32)
    admin_in_update = AdminUpdate(api_key=new_api_key)
    await crud.admin.update(db_tests, db_obj=created_admin, obj_in=admin_in_update)
    updated_admin = await crud.admin.get(db_tests, id=created_admin.id)
    assert updated_admin
    assert created_admin.email == updated_admin.email
    assert verify_password(new_api_key, updated_admin.hashed_api_key)


async def test_update_admin_using_dict(db_tests: AsyncSession) -> None:
    created_admin = await ut.create_random_admin(db_tests)
    new_api_key = ut.random_lower_string(32)
    admin_in_update = {"api_key": new_api_key}
    await crud.admin.update(db_tests, db_obj=created_admin, obj_in=admin_in_update)
    updated_admin = await crud.admin.get(db_tests, id=created_admin.id)
    assert updated_admin
    assert created_admin.email == updated_admin.email
    assert verify_password(new_api_key, updated_admin.hashed_api_key)


async def test_remove_admin(db_tests: AsyncSession) -> None:
    created_admin = await ut.create_random_admin(db_tests)
    await crud.admin.remove(db_tests, id=created_admin.id)
    removed_admin = await crud.admin.get(db_tests, id=created_admin.id)
    assert removed_admin is None
