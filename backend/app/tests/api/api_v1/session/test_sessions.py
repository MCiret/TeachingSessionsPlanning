import datetime as dt

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.encoders import jsonable_encoder

from app.core.config import settings
from app.tests import utils_for_testing as ut
from app import crud
from app.schemas import SessionCreate, SessionTypeCreate, SessionStatusCreate

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
    """Unnecessary test that actually tests the Depends() which is already tested in test_deps.py."""
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
    """Unnecessary test that actually tests the Depends() which is already tested in test_deps.py."""
    r = await async_client.get(f"{settings.API_V1_STR}/sessions/mine", headers=admin_token_headers)
    assert r.status_code == 400
    assert "To do this, the user has to be a Speaker or Participant user" in r.json().values()


@pytest.fixture
async def mock_spk_is_free(request, mocker):
    mock_is_free = mocker.patch('app.crud.speaker.is_free_for_session')
    mock_is_free.return_value = request.node.get_closest_marker("is_free_bool").args[0]
    return mock_is_free


@pytest.fixture
async def db_session_type_status(db_tests: AsyncSession) -> dict:
    s_type = await crud.session_type.create(db_tests, obj_in=SessionTypeCreate(name="s_type_name"))
    s_status = await crud.session_status.create(db_tests, obj_in=SessionStatusCreate(name="s_status_name"))
    yield {"s_type": s_type, "s_status": s_status}
    await crud.session_type.remove(db_tests, id=s_type.id)
    await crud.session_status.remove(db_tests, id=s_status.id)


@pytest.mark.is_free_bool(True)
async def test_create_session_by_participant(async_client: AsyncClient, db_tests: AsyncSession,
                                             mock_spk_is_free, db_session_type_status) -> None:
    s_type = db_session_type_status["s_type"]
    s_status = db_session_type_status["s_status"]
    speaker = await ut.create_random_speaker(db_tests)
    participant = await ut.create_random_participant(db_tests, speaker_id=speaker.id)
    participant_token_headers = await ut.participant_authentication_token_from_email(client=async_client,
                                                                                     email=participant.email,
                                                                                     db=db_tests)
    data = jsonable_encoder(SessionCreate(date=dt.date(2022, 1, 31), time=dt.time(9, 30),
                                          comments="Session create endpoint",
                                          type_name=s_type.name, status_name=s_status.name))
    r = await async_client.post(f"{settings.API_V1_STR}/sessions", headers=participant_token_headers, json=data)
    assert r.status_code == 200
    assert mock_spk_is_free.called
    r_session = r.json()
    db_session = await crud.session.get(db_tests, id=r_session["id"])
    assert (db_session and db_session.participant_id == participant.id
            and db_session.date == dt.date(2022, 1, 31))
    await crud.session.remove(db_tests, id=db_session.id)


@pytest.mark.is_free_bool(True)
async def test_create_session_by_speaker(async_client: AsyncClient, db_tests: AsyncSession,
                                         mock_spk_is_free, db_session_type_status) -> None:
    s_type = db_session_type_status["s_type"]
    s_status = db_session_type_status["s_status"]
    speaker = await ut.create_random_speaker(db_tests)
    participant = await ut.create_random_participant(db_tests, speaker_id=speaker.id)
    speaker_token_headers = await ut.speaker_authentication_token_from_email(client=async_client, email=speaker.email,
                                                                             db=db_tests)
    data = jsonable_encoder(SessionCreate(date=dt.date(2022, 2, 21), time=dt.time(15, 30),
                                          comments="Session create endpoint", participant_id=participant.id,
                                          type_name=s_type.name, status_name=s_status.name))
    r = await async_client.post(f"{settings.API_V1_STR}/sessions", headers=speaker_token_headers, json=data)
    assert r.status_code == 200
    assert mock_spk_is_free.called
    r_session = r.json()
    db_session = await crud.session.get(db_tests, id=r_session["id"])
    assert (db_session and db_session.participant_id == participant.id
            and db_session.date == dt.date(2022, 2, 21))
    await crud.session.remove(db_tests, id=db_session.id)


@pytest.mark.is_free_bool(False)
async def test_create_session_speaker_not_free(async_client: AsyncClient, db_tests: AsyncSession,
                                               mock_spk_is_free, db_session_type_status) -> None:
    s_type = db_session_type_status["s_type"]
    s_status = db_session_type_status["s_status"]
    speaker = await ut.create_random_speaker(db_tests)
    participant = await ut.create_random_participant(db_tests, speaker_id=speaker.id)
    participant_token_headers = await ut.participant_authentication_token_from_email(client=async_client,
                                                                                     email=participant.email,
                                                                                     db=db_tests)
    data = jsonable_encoder(SessionCreate(date=dt.date(2022, 4, 22), time=dt.time(17),
                                          comments="Session create endpoint",
                                          type_name=s_type.name, status_name=s_status.name))
    r = await async_client.post(f"{settings.API_V1_STR}/sessions", headers=participant_token_headers, json=data)
    assert r.status_code == 400
    assert mock_spk_is_free.called
    assert ("Cannot create this session. Please, check if Speaker has corresponding availability "
            "and if there is no session that already exists...") in r.json().values()
