import pytest
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.schemas import SpeakerUpdate
from app.core.security import verify_password
from app.tests import utils as ut

# This is the same as using the @pytest.mark.anyio on all test functions in the module
pytestmark = pytest.mark.anyio


async def test_create_speaker(db_tests: AsyncSession) -> None:
    email = ut.random_email()
    created_speaker = await ut.create_random_speaker(db_tests, email=email)
    assert created_speaker.email == email
    assert created_speaker.profile == "speaker"
    assert hasattr(created_speaker, "hashed_api_key")


async def test_get_speaker(db_tests: AsyncSession) -> None:
    created_speaker = await ut.create_random_speaker(db_tests)
    got_speaker = await crud.speaker.get(db_tests, id=created_speaker.id)
    assert got_speaker
    assert got_speaker.profile == "speaker"
    assert created_speaker.email == got_speaker.email
    assert jsonable_encoder(created_speaker) == jsonable_encoder(got_speaker)


async def test_update_speaker(db_tests: AsyncSession) -> None:
    created_speaker = await ut.create_random_speaker(db_tests)
    new_api_key = ut.random_lower_string(32)
    speaker_in_update = SpeakerUpdate(api_key=new_api_key)
    await crud.speaker.update(db_tests, db_obj=created_speaker, obj_in=speaker_in_update)
    updated_speaker = await crud.speaker.get(db_tests, id=created_speaker.id)
    assert updated_speaker
    assert created_speaker.email == updated_speaker.email
    assert verify_password(new_api_key, updated_speaker.hashed_api_key)


async def test_remove_speaker(db_tests: AsyncSession) -> None:
    created_speaker = await ut.create_random_speaker(db_tests)
    await crud.speaker.remove(db_tests, id=created_speaker.id)
    removed_speaker = await crud.speaker.get(db_tests, id=created_speaker.id)
    assert removed_speaker is None


async def test_get_by_participant_id(db_tests: AsyncSession) -> None:
    speaker = await ut.create_random_speaker(db_tests)
    participant = await ut.create_random_participant(db_tests, speaker_id=speaker.id)
    db_speaker = await crud.speaker.get_by_participant_id(db_tests, participant_id=participant.id)
    assert db_speaker.id == speaker.id
