import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.encoders import jsonable_encoder

from app.core.config import settings
from app import crud
from app.schemas import ParticipantCreate, ParticipantUpdate
from app.tests import utils as ut

# This is the same as using the @pytest.mark.anyio on all test functions in the module
pytestmark = pytest.mark.anyio


async def test_read_participants_by_admin_or_speaker(async_client: AsyncClient, db_tests: AsyncSession,
                                                     admin_token_headers: dict[str, str],
                                                     speaker_token_headers: dict[str, str]) -> None:
    await ut.create_random_participant(db_tests)
    await ut.create_random_participant(db_tests)
    await ut.create_random_speaker(db_tests)
    await ut.create_random_admin(db_tests)
    r = await async_client.get(f"{settings.API_V1_STR}/users/participants/", headers=admin_token_headers)
    r2 = await async_client.get(f"{settings.API_V1_STR}/users/participants/", headers=speaker_token_headers)
    r_participants = r.json(), r2.json()
    for participants in r_participants:
        assert len(participants) >= 2
        for p in participants:
            assert "email" in p
            assert p["profile"] == "participant"


async def test_read_participants_by_not_admin_nor_speaker(async_client: AsyncClient, db_tests: AsyncSession,
                                                          participant_token_headers: dict[str, str]) -> None:
    await ut.create_random_participant(db_tests)
    await ut.create_random_speaker(db_tests)
    await ut.create_random_admin(db_tests)
    r = await async_client.get(f"{settings.API_V1_STR}/users/participants/", headers=participant_token_headers)
    assert r.status_code == 400
    assert "To do this, the user has to be a Speaker or Admin user" in r.json().values()


async def test_create_participant_by_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                           admin_token_headers: dict[str, str]) -> None:
    db_existing_speaker_id = (await ut.create_random_speaker(db_tests)).id
    data = jsonable_encoder(ParticipantCreate(email=ut.random_email(),
                                              api_key=ut.random_lower_string(32),
                                              first_name=ut.random_lower_string(8),
                                              last_name=ut.random_lower_string(8),
                                              type_name="initial",
                                              speaker_id=db_existing_speaker_id))
    r = await async_client.post(f"{settings.API_V1_STR}/users/participants/participant",
                                headers=admin_token_headers, json=data)
    assert r.status_code == 200
    db_participant_dict = r.json()
    assert "email" in db_participant_dict
    db_participant = await crud.participant.get(db_tests, id=db_participant_dict["id"])
    assert db_participant.email == data["email"] and db_participant.speaker_id == db_existing_speaker_id


async def test_create_participant_by_speaker(async_client: AsyncClient, db_tests: AsyncSession) -> None:
    db_speaker = await ut.create_random_speaker(db_tests)
    token = await ut.speaker_authentication_token_from_email(client=async_client, email=db_speaker.email, db=db_tests)
    data = jsonable_encoder(ParticipantCreate(email=ut.random_email(),
                                              api_key=ut.random_lower_string(32),
                                              first_name=ut.random_lower_string(8),
                                              last_name=ut.random_lower_string(8),
                                              type_name="initial"))
    r = await async_client.post(f"{settings.API_V1_STR}/users/participants/participant", headers=token, json=data)
    assert r.status_code == 200
    db_participant_dict = r.json()
    assert "email" in db_participant_dict
    db_participant = await crud.participant.get(db_tests, id=db_participant_dict["id"])
    assert db_participant.email == data["email"] and db_participant.speaker_id == db_speaker.id


async def test_create_participant_not_existing_type_name_by_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                                                  admin_token_headers: dict[str, str]) -> None:
    db_existing_speaker_id = (await ut.create_random_speaker(db_tests)).id
    email = ut.random_email()
    data = jsonable_encoder(ParticipantCreate(email=email,
                                              api_key=ut.random_lower_string(32),
                                              first_name=ut.random_lower_string(8),
                                              last_name=ut.random_lower_string(8),
                                              type_name="not existing in db",
                                              speaker_id=db_existing_speaker_id))
    r = await async_client.post(f"{settings.API_V1_STR}/users/participants/participant",
                                headers=admin_token_headers, json=data)
    assert r.status_code == 400
    assert f"Type {data['type_name']} does not exists..." in r.json().values()
    assert not await crud.participant.get_by_email(db_tests, email=email)


async def test_create_participant_not_existing_status_name_by_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                                                    admin_token_headers: dict[str, str]) -> None:
    db_existing_speaker_id = (await ut.create_random_speaker(db_tests)).id
    email = ut.random_email()
    data = jsonable_encoder(ParticipantCreate(email=email,
                                              api_key=ut.random_lower_string(32),
                                              first_name=ut.random_lower_string(8),
                                              last_name=ut.random_lower_string(8),
                                              type_name="initial",
                                              status_name="not existing in db",
                                              speaker_id=db_existing_speaker_id))
    r = await async_client.post(f"{settings.API_V1_STR}/users/participants/participant",
                                headers=admin_token_headers, json=data)
    assert r.status_code == 400
    assert f"Status {data['status_name']} does not exists..." in r.json().values()
    assert not await crud.participant.get_by_email(db_tests, email=email)


async def test_create_participant_not_existing_speaker_id_by_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                                                   admin_token_headers: dict[str, str]) -> None:
    # get a not existing speaker id
    db_speakers = await crud.speaker.get_multi(db_tests)
    if db_speakers:
        max_id = max([speaker.id for speaker in db_speakers])
    else:
        max_id = 0
    data = jsonable_encoder(ParticipantCreate(email=ut.random_email(),
                                              api_key=ut.random_lower_string(32),
                                              first_name=ut.random_lower_string(8),
                                              last_name=ut.random_lower_string(8),
                                              type_name="initial",
                                              speaker_id=max_id + 1))
    r = await async_client.post(f"{settings.API_V1_STR}/users/participants/participant",
                                headers=admin_token_headers, json=data)
    assert r.status_code == 400
    assert "A speaker user with this id does not exist in the system..." in r.json().values()


async def test_create_participant_missing_speaker_id_by_admin(async_client: AsyncClient,
                                                              admin_token_headers: dict[str, str]) -> None:
    data = jsonable_encoder(ParticipantCreate(email=ut.random_email(),
                                              api_key=ut.random_lower_string(32),
                                              first_name=ut.random_lower_string(8),
                                              last_name=ut.random_lower_string(8),
                                              type_name="initial"))
    r = await async_client.post(f"{settings.API_V1_STR}/users/participants/participant",
                                headers=admin_token_headers, json=data)
    assert r.status_code == 400
    assert "If you are not a Speaker user, you have to set the speaker_id value..." in r.json().values()


async def test_create_participant_existing_email_by_admin_or_speaker(async_client: AsyncClient, db_tests: AsyncSession,
                                                                     admin_token_headers: dict[str, str],
                                                                     speaker_token_headers: dict[str, str]) -> None:
    email = ut.random_email()
    existing_email_user = await ut.create_random_participant(db_tests, email=email)
    db_existing_speaker_id = (await ut.create_random_speaker(db_tests)).id
    data = jsonable_encoder(ParticipantCreate(email=email,
                                              api_key=ut.random_lower_string(32),
                                              first_name=ut.random_lower_string(8),
                                              last_name=ut.random_lower_string(8),
                                              type_name="initial",
                                              speaker_id=db_existing_speaker_id))
    r = await async_client.post(f"{settings.API_V1_STR}/users/participants/participant",
                                headers=admin_token_headers, json=data)
    r2 = await async_client.post(f"{settings.API_V1_STR}/users/participants/participant",
                                 headers=speaker_token_headers, json=data)
    assert r.status_code == 400 and r2.status_code == 400
    assert "A user with this email already exists in the system..." in r.json().values()
    assert "A user with this email already exists in the system..." in r2.json().values()
    db_existing_email_user = await crud.user.get(db_tests, id=existing_email_user.id)
    assert db_existing_email_user.email == existing_email_user.email


async def test_update_participant_by_id_by_admin_or_speaker(async_client: AsyncClient, db_tests: AsyncSession,
                                                            admin_token_headers: dict[str, str],
                                                            speaker_token_headers: dict[str, str]) -> None:
    db_participant = await ut.create_random_participant(db_tests)
    db_participant2 = await ut.create_random_participant(db_tests)
    data = jsonable_encoder(ParticipantUpdate(first_name="Sandra"), exclude_unset=True)
    r = await async_client.put(f"{settings.API_V1_STR}/users/participants/{db_participant.id}",
                               headers=admin_token_headers, json=data)
    r2 = await async_client.put(f"{settings.API_V1_STR}/users/participants/{db_participant2.id}",
                                headers=speaker_token_headers, json=data)
    assert r.status_code == 200 and r2.status_code == 200
    assert "Sandra" in r.json().values() and "Sandra" in r2.json().values()
    # db_tests (i.e SQLAlchemy AsyncSession) is not closed before the end of the tests session
    await db_tests.refresh(db_participant)
    await db_tests.refresh(db_participant2)
    assert (await crud.participant.get(db_tests, id=db_participant.id)).first_name == "Sandra"
    assert (await crud.participant.get(db_tests, id=db_participant2.id)).first_name == "Sandra"


async def test_update_participant_by_id_existing_email_by_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                                                admin_token_headers: dict[str, str]) -> None:
    email = ut.random_email()
    await ut.create_random_participant(db_tests, email=email)
    participant_to_update = await ut.create_random_participant(db_tests)
    data = jsonable_encoder(ParticipantUpdate(first_name="Sandra", email=email), exclude_unset=True)
    r = await async_client.put(f"{settings.API_V1_STR}/users/participants/{participant_to_update.id}",
                               headers=admin_token_headers, json=data)
    assert r.status_code == 400
    assert "A user with this email already exists in the system..." in r.json().values()


async def test_update_participant_by_id_not_existing_by_admin(async_client: AsyncClient, db_tests: AsyncSession,
                                                              admin_token_headers: dict[str, str]) -> None:
    # get a not existing participant id
    db_participants = await crud.participant.get_multi(db_tests)
    if db_participants:
        max_id = max([participant.id for participant in db_participants])
    else:
        max_id = 0
    data = jsonable_encoder(ParticipantUpdate(first_name="Sandra"), exclude_unset=True)
    r = await async_client.put(f"{settings.API_V1_STR}/users/participants/{max_id + 1}",
                               headers=admin_token_headers, json=data)
    assert r.status_code == 404
    assert "A participant user with this id does not exist in the system..." in r.json().values()


async def test_update_participant_by_id_not_existing_speaker_id_by_admin(async_client: AsyncClient,
                                                                         db_tests: AsyncSession,
                                                                         admin_token_headers: dict[str, str]) -> None:
    db_participant = await ut.create_random_participant(db_tests)
    # get a not existing speaker id
    db_speakers = await crud.speaker.get_multi(db_tests)
    if db_speakers:
        max_id = max([speaker.id for speaker in db_speakers])
    else:
        max_id = 0
    data = jsonable_encoder(ParticipantUpdate(first_name="Sandra", speaker_id=max_id + 1), exclude_unset=True)
    r = await async_client.put(f"{settings.API_V1_STR}/users/participants/{db_participant.id}",
                               headers=admin_token_headers, json=data)
    assert r.status_code == 400
    assert "A speaker user with this id does not exist in the system..." in r.json().values()


async def test_update_participant_by_id_not_existing_type_name_by_admin(async_client: AsyncClient,
                                                                        db_tests: AsyncSession,
                                                                        admin_token_headers: dict[str, str]) -> None:
    db_participant = await ut.create_random_participant(db_tests)
    data = jsonable_encoder(ParticipantUpdate(first_name="Sandra", type_name="not existing in db"), exclude_unset=True)
    r = await async_client.put(f"{settings.API_V1_STR}/users/participants/{db_participant.id}",
                               headers=admin_token_headers, json=data)
    assert r.status_code == 400
    assert f"Type {data['type_name']} does not exists..." in r.json().values()


async def test_update_participant_by_id_not_existing_status_name_by_admin(async_client: AsyncClient,
                                                                          db_tests: AsyncSession,
                                                                          admin_token_headers: dict[str, str]) -> None:
    db_participant = await ut.create_random_participant(db_tests)
    data = jsonable_encoder(ParticipantUpdate(first_name="Sandra", status_name="not existing in db"),
                            exclude_unset=True)
    r = await async_client.put(f"{settings.API_V1_STR}/users/participants/{db_participant.id}",
                               headers=admin_token_headers, json=data)
    assert r.status_code == 400
    assert f"Status {data['status_name']} does not exists..." in r.json().values()


async def test_update_participant_by_id_by_not_admin_nor_speaker(async_client: AsyncClient, db_tests: AsyncSession,
                                                                 participant_token_headers: dict[str, str]) -> None:
    db_participant = await ut.create_random_participant(db_tests)
    data = jsonable_encoder(ParticipantUpdate(first_name="Sandra"), exclude_unset=True)
    r = await async_client.put(f"{settings.API_V1_STR}/users/participants/{db_participant.id}",
                               headers=participant_token_headers, json=data)
    assert r.status_code == 400
    assert "To do this, the user has to be a Speaker or Admin user" in r.json().values()
