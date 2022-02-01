import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.encoders import jsonable_encoder

from app.core.config import settings
from app import crud
from app.schemas import SpeakerCreate, SpeakerUpdate
from app.tests import utils_for_testing as ut

# This is the same as using the @pytest.mark.anyio on all test functions in the module
pytestmark = pytest.mark.anyio


async def test_read_speakers_by_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                      admin_token_headers: dict[str, str]) -> None:
    await ut.create_random_participant(db_tests)
    await ut.create_random_speaker(db_tests)
    await ut.create_random_admin(db_tests)
    r = await async_client.get(f"{settings.API_V1_STR}/users/speakers/", headers=admin_token_headers)
    speakers = r.json()
    assert len(speakers) >= 1
    for speaker in speakers:
        assert "email" in speaker
        assert speaker["profile"] == "speaker"


async def test_read_speakers_by_not_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                          speaker_token_headers: dict[str, str]) -> None:
    """Unnecessary test that actually tests the Depends() which is already tested in test_deps.py."""
    await ut.create_random_participant(db_tests)
    await ut.create_random_speaker(db_tests)
    await ut.create_random_admin(db_tests)
    r = await async_client.get(f"{settings.API_V1_STR}/users/speakers/", headers=speaker_token_headers)
    assert r.status_code == 400
    assert "The user doesn't have enough privileges" in r.json().values()


async def test_create_speaker_by_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                       admin_token_headers: dict[str, str]) -> None:
    data = jsonable_encoder(SpeakerCreate(email=ut.random_email(),
                                          api_key=ut.random_lower_string(32),
                                          first_name=ut.random_lower_string(8),
                                          last_name=ut.random_lower_string(8),
                                          slot_time=ut.random_five_multiple_number()))
    r = await async_client.post(f"{settings.API_V1_STR}/users/speaker", headers=admin_token_headers, json=data)
    assert r.status_code == 200
    db_speaker_dict = r.json()
    assert "email" in db_speaker_dict
    db_speaker = await crud.speaker.get(db_tests, id=db_speaker_dict["id"])
    assert db_speaker.email == data["email"]


async def test_create_speaker_existing_email_by_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                                      admin_token_headers: dict[str, str]) -> None:
    email = ut.random_email()
    existing_email_user = await ut.create_random_participant(db_tests, email=email)
    data = jsonable_encoder(SpeakerCreate(email=email,
                                          api_key=ut.random_lower_string(32),
                                          first_name=ut.random_lower_string(8),
                                          last_name=ut.random_lower_string(8),
                                          slot_time=ut.random_five_multiple_number()))
    r = await async_client.post(f"{settings.API_V1_STR}/users/speaker", headers=admin_token_headers, json=data)
    assert r.status_code == 400
    assert "A user with this email already exists in the system..." in r.json().values()
    db_existing_email_user = await crud.user.get(db_tests, id=existing_email_user.id)
    assert db_existing_email_user.email == existing_email_user.email


async def test_create_speaker_by_not_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                           speaker_token_headers: dict[str, str]) -> None:
    """Unnecessary test that actually tests the Depends() which is already tested in test_deps.py."""
    email = ut.random_email()
    data = jsonable_encoder(SpeakerCreate(email=email,
                                          api_key=ut.random_lower_string(32),
                                          first_name=ut.random_lower_string(8),
                                          last_name=ut.random_lower_string(8),
                                          slot_time=ut.random_five_multiple_number()))
    r = await async_client.post(f"{settings.API_V1_STR}/users/speaker", headers=speaker_token_headers, json=data)
    assert r.status_code == 400
    assert "The user doesn't have enough privileges" in r.json().values()
    not_created_db_speaker = await crud.user.get_by_email(db_tests, email=email)
    assert not not_created_db_speaker


async def test_update_speaker_by_id_by_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                             admin_token_headers: dict[str, str]) -> None:
    db_speaker = await ut.create_random_speaker(db_tests)
    data = jsonable_encoder(SpeakerUpdate(first_name="Sandra"), exclude_unset=True)
    r = await async_client.put(f"{settings.API_V1_STR}/users/speaker/{db_speaker.id}",
                               headers=admin_token_headers, json=data)
    assert r.status_code == 200
    assert "Sandra" in r.json().values()


async def test_update_speaker_by_id_existing_email_by_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                                            admin_token_headers: dict[str, str]) -> None:
    db_speaker = await ut.create_random_speaker(db_tests)
    data = jsonable_encoder(SpeakerUpdate(first_name="Sandra", email=db_speaker.email), exclude_unset=True)
    r = await async_client.put(f"{settings.API_V1_STR}/users/speaker/{db_speaker.id}",
                               headers=admin_token_headers, json=data)
    assert r.status_code == 400
    assert "A user with this email already exists in the system..." in r.json().values()


async def test_update_speaker_by_id_not_existing_by_admin(async_client: AsyncClient,
                                                          admin_token_headers: dict[str, str]) -> None:
    data = jsonable_encoder(SpeakerUpdate(first_name="Sandra"), exclude_unset=True)
    r = await async_client.put(f"{settings.API_V1_STR}/users/speaker/-1",
                               headers=admin_token_headers, json=data)
    assert r.status_code == 404
    assert "A speaker user with this id does not exist in the system..." in r.json().values()


async def test_update_speaker_by_id_by_not_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                                 speaker_token_headers: dict[str, str]) -> None:
    """Unnecessary test that actually tests the Depends() which is already tested in test_deps.py."""
    db_speaker = await ut.create_random_speaker(db_tests)
    data = jsonable_encoder(SpeakerUpdate(first_name="Sandra"), exclude_unset=True)
    r = await async_client.put(f"{settings.API_V1_STR}/users/speaker/{db_speaker.id}",
                               headers=speaker_token_headers, json=data)
    assert r.status_code == 400
    assert "The user doesn't have enough privileges" in r.json().values()
