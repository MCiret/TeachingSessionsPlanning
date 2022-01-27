"""
Test crud operations that are common for all type of user (admin/speaker/participant) :
- authentication ;
- is active or not
- is admin or not
For these tests, a speaker user is used as "normal" user (i.e not admin).
"""

import pytest
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.core.security import verify_password
from app.schemas import UserCreate, SpeakerCreate, SpeakerUpdate
from app.tests import utils as ut

# This is the same as using the @pytest.mark.anyio on all test functions in the module
pytestmark = pytest.mark.anyio


async def test_authenticate_user(db_tests: AsyncSession) -> None:
    email = ut.random_email()
    api_key = ut.random_lower_string(32)
    user = await ut.create_random_speaker(db_tests, email=email, api_key=api_key)
    authenticated_user = await crud.user.authenticate(db_tests, email=email, api_key=api_key)
    assert authenticated_user
    assert user.email == authenticated_user.email


async def test_authenticate_user_not_existing(db_tests: AsyncSession) -> None:
    email = ut.random_email()
    api_key = ut.random_lower_string(32)
    user = await crud.user.authenticate(db_tests, email=email, api_key=api_key)
    assert user is None


async def test_authenticate_user_using_wrong_api_key(db_tests: AsyncSession) -> None:
    email = ut.random_email()
    api_key = ut.random_lower_string(32)
    user = await ut.create_random_speaker(db_tests, email=email, api_key=api_key)
    user = await crud.user.authenticate(db_tests, email=email, api_key=api_key[3:])
    assert user is None


async def test_is_active_user(db_tests: AsyncSession) -> None:
    user = await ut.create_random_speaker(db_tests)
    is_active = await crud.user.is_active(user)
    assert is_active is True


async def test_is_active_user_inactive(db_tests: AsyncSession) -> None:
    user_in = SpeakerCreate(
        email=ut.random_email(), is_active=False,
        api_key=ut.random_lower_string(32), first_name=ut.random_lower_string(6),
        last_name=ut.random_lower_string(6), slot_time=ut.random_five_multiple_number())
    user = await crud.speaker.create(db=db_tests, obj_in=user_in)
    is_active = await crud.user.is_active(user)
    assert is_active is False


async def test_is_admin_user(db_tests: AsyncSession) -> None:
    admin_user = await ut.create_random_admin(db_tests)
    is_admin_user = await crud.user.is_admin(admin_user)
    assert is_admin_user is True


async def test_is_admin_user_normal_user(db_tests: AsyncSession) -> None:
    not_admin_user = await ut.create_random_speaker(db_tests)
    is_admin_user = await crud.user.is_admin(not_admin_user)
    assert is_admin_user is False


async def test_is_speaker(db_tests: AsyncSession) -> None:
    user = await ut.create_random_speaker(db_tests)
    is_speaker = await crud.user.is_speaker(user)
    assert is_speaker is True


async def test_is_speaker_not_speaker_user(db_tests: AsyncSession) -> None:
    not_speaker_user = await ut.create_random_admin(db_tests)
    is_speaker = await crud.user.is_speaker(not_speaker_user)
    assert is_speaker is False


async def test_is_participant(db_tests: AsyncSession) -> None:
    user = await ut.create_random_participant(db_tests)
    is_participant = await crud.user.is_participant(user)
    assert is_participant is True


async def test_is_participant_not_participant_user(db_tests: AsyncSession) -> None:
    not_speaker_user = await ut.create_random_admin(db_tests)
    is_participant = await crud.user.is_participant(not_speaker_user)
    assert is_participant is False


async def test_create_user_raise_NotImplementedError(db_tests: AsyncSession):
    with pytest.raises(NotImplementedError):
        await crud.user.create(db_tests, obj_in=UserCreate(email="user@email.com", api_key="apikeyuser",
                               first_name="user first name", last_name="user last name"))


async def test_get_user(db_tests: AsyncSession) -> None:
    user = await ut.create_random_speaker(db_tests)
    got_user = await crud.user.get(db_tests, id=user.id)
    assert got_user
    assert user.email == got_user.email
    assert jsonable_encoder(user) == jsonable_encoder(got_user)


async def test_get_multi_user(db_tests: AsyncSession) -> None:
    await ut.create_random_speaker(db_tests)
    await ut.create_random_speaker(db_tests)
    await ut.create_random_speaker(db_tests)
    got_multi_users_dicts = await crud.user.get_multi(db_tests)
    assert len(got_multi_users_dicts) >= 3


async def test_update_user(db_tests: AsyncSession):
    user = await ut.create_random_speaker(db_tests)
    new_api_key = ut.random_lower_string(32)
    user_in_update = SpeakerUpdate(api_key=new_api_key)
    await crud.user.update(db_tests, db_obj=user, obj_in=user_in_update)
    updated_user = await crud.user.get(db_tests, id=user.id)
    assert updated_user
    assert user.email == updated_user.email
    assert verify_password(new_api_key, updated_user.hashed_api_key)


async def test_remove_user(db_tests: AsyncSession) -> None:
    user = await ut.create_random_speaker(db_tests)
    await crud.user.remove(db_tests, id=user.id)
    removed_user = await crud.user.get(db_tests, id=user.id)
    removed_speaker = await crud.speaker.get(db_tests, id=user.id)
    assert removed_user is None
    assert removed_speaker is None
