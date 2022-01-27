import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.encoders import jsonable_encoder

from app.core.config import settings
from app.tests import utils as ut
from app import crud

# This is the same as using the @pytest.mark.anyio on all test functions in the module
pytestmark = pytest.mark.anyio


async def test_read_sessions_by_admin_or_speaker(async_client: AsyncClient, db_tests: AsyncSession,
                                                 admin_token_headers: dict[str, str]) -> None:
    s1 = await ut.create_random_session(db_tests)
    s2 = await ut.create_random_session(db_tests)
    s3 = await ut.create_random_session(db_tests)
    r = await async_client.get(f"{settings.API_V1_STR}/sessions/", headers=admin_token_headers)
    r2 = await async_client.get(f"{settings.API_V1_STR}/sessions/", headers=admin_token_headers)
    r_sessions = r.json(), r2.json()
    for sessions in r_sessions:
        assert len(sessions) >= 3
        for session in sessions:
            assert "comments" in session
    await crud.session.remove(db_tests, id=s1.id)
    await crud.session.remove(db_tests, id=s2.id)
    await crud.session.remove(db_tests, id=s3.id)


async def test_read_sessions_by_not_admin_nor_speaker(async_client: AsyncClient, db_tests: AsyncSession,
                                                      participant_token_headers: dict[str, str]) -> None:
    s1 = await ut.create_random_session(db_tests)
    s2 = await ut.create_random_session(db_tests)
    s3 = await ut.create_random_session(db_tests)
    r = await async_client.get(f"{settings.API_V1_STR}/sessions/", headers=participant_token_headers)
    assert r.status_code == 400
    assert "To do this, the user has to be a Speaker or Admin user" in r.json().values()
    await crud.session.remove(db_tests, id=s1.id)
    await crud.session.remove(db_tests, id=s2.id)
    await crud.session.remove(db_tests, id=s3.id)


async def test_read_sessions_mine_by_speaker_or_participant(async_client: AsyncClient, db_tests: AsyncSession) -> None:
    speaker = await ut.create_random_speaker(db_tests)
    participant = await ut.create_random_participant(db_tests, speaker_id=speaker.id)
    speaker_token_headers = await ut.speaker_authentication_token_from_email(client=async_client,
                                                                             email=speaker.email, db=db_tests)
    participant_token_headers = await ut.participant_authentication_token_from_email(client=async_client,
                                                                                     email=participant.email,
                                                                                     db=db_tests)

    s1 = await ut.create_random_session(db_tests, participant_id=participant.id)
    s2 = await ut.create_random_session(db_tests, participant_id=participant.id)
    s3 = await ut.create_random_session(db_tests, participant_id=participant.id)

    r = await async_client.get(f"{settings.API_V1_STR}/sessions/mine", headers=speaker_token_headers)
    r2 = await async_client.get(f"{settings.API_V1_STR}/sessions/mine", headers=participant_token_headers)
    r_sessions = r.json(), r2.json()
    for sessions in r_sessions:
        assert len(sessions) >= 3
        assert participant.id in [s["participant_id"] for s in sessions]
        assert (s1.id and s2.id and s3.id) in [s["id"] for s in sessions]
    await crud.session.remove(db_tests, id=s1.id)
    await crud.session.remove(db_tests, id=s2.id)
    await crud.session.remove(db_tests, id=s3.id)


async def test_read_sessions_mine_by_not_speaker_nor_participant(async_client: AsyncClient,
                                                                 admin_token_headers: dict[str, str]) -> None:
    r = await async_client.get(f"{settings.API_V1_STR}/sessions/mine", headers=admin_token_headers)
    assert r.status_code == 400
    assert "To do this, the user has to be a Speaker or Participant user" in r.json().values()
