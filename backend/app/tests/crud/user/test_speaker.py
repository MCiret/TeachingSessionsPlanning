import datetime as dt

import pytest
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.schemas import SpeakerUpdate
from app.core.security import verify_password
from app.tests import utils as ut
from app.models import ParticipantType
from app.schemas import ParticipantTypeCreate, AvailabilityCreate

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


@pytest.fixture
async def db_data(db_tests: AsyncSession) -> ParticipantType:
    p_type_1sw = await crud.participant_type.create(db_tests, obj_in=ParticipantTypeCreate(name="one_sw",
                                                                                           nb_session_week=1))
    p_type_2sw = await crud.participant_type.create(db_tests, obj_in=ParticipantTypeCreate(name="two_sw",
                                                                                           nb_session_week=2))
    speaker = await ut.create_random_speaker(db_tests, slot_time=30)
    p_1sw = await ut.create_random_participant(db_tests, speaker_id=speaker.id, p_type_name="one_sw")
    p_2sw = await ut.create_random_participant(db_tests, speaker_id=speaker.id, p_type_name="two_sw")

    yield {"speaker": speaker, "p_1sw": p_1sw, "p_2sw": p_2sw}

    await crud.participant.remove(db_tests, id=p_1sw.id)
    await crud.participant.remove(db_tests, id=p_2sw.id)
    await crud.participant_type.remove(db_tests, id=p_type_1sw.id)
    await crud.participant_type.remove(db_tests, id=p_type_2sw.id)


async def test_get_sessions_times_by_date(db_tests: AsyncSession, db_data) -> None:
    s1_p_1sw = await ut.create_random_session(db_tests, participant_id=db_data["p_1sw"].id,
                                              date_=dt.date(2022, 1, 27), time_=dt.time(9))
    s2_p_1sw = await ut.create_random_session(db_tests, participant_id=db_data["p_1sw"].id,
                                              date_=dt.date(2022, 2, 15), time_=dt.time(10))

    s1_p_2sw = await ut.create_random_session(db_tests, participant_id=db_data["p_2sw"].id,
                                              date_=dt.date(2022, 2, 15), time_=dt.time(10, 30))
    s2_p_2sw = await ut.create_random_session(db_tests, participant_id=db_data["p_2sw"].id,
                                              date_=dt.date(2022, 2, 15), time_=dt.time(14, 30))

    assert not await crud.speaker.get_sessions_times_by_date(db_tests, db_obj=db_data["speaker"],
                                                             date=dt.date(2022, 2, 12))
    spk_sessions_times_list = await crud.speaker.get_sessions_times_by_date(db_tests, db_obj=db_data["speaker"],
                                                                            date=dt.date(2022, 2, 15))
    assert len(spk_sessions_times_list) == 5
    assert (dt.time(10) and dt.time(10, 30) and dt.time(11)
            and dt.time(14, 30) and dt.time(15)) in spk_sessions_times_list
    assert dt.time(9) not in spk_sessions_times_list
    await crud.session.remove(db_tests, id=s1_p_1sw.id)
    await crud.session.remove(db_tests, id=s2_p_1sw.id)
    await crud.session.remove(db_tests, id=s1_p_2sw.id)
    await crud.session.remove(db_tests, id=s2_p_2sw.id)


async def test_get_free_sessions_times_by_date(db_tests: AsyncSession, db_data) -> None:
    speaker = db_data["speaker"]
    av1_in = AvailabilityCreate(start_date=dt.date(2021, 12, 1),
                                end_date=dt.date(2022, 3, 31),
                                week_day=3,
                                time=dt.time(9))
    av2_in = AvailabilityCreate(start_date=dt.date(2022, 2, 1),
                                end_date=dt.date(2022, 5, 31),
                                week_day=3,
                                time=dt.time(10))
    av3_in = AvailabilityCreate(start_date=dt.date(2022, 3, 15),
                                end_date=dt.date(2022, 7, 31),
                                week_day=3,
                                time=dt.time(14))
    av4_in = AvailabilityCreate(start_date=dt.date(2022, 3, 15),
                                end_date=dt.date(2022, 7, 31),
                                week_day=2,
                                time=dt.time(10))
    av1 = await crud.availability.create(db_tests, obj_in=av1_in, speaker_id=speaker.id)
    av2 = await crud.availability.create(db_tests, obj_in=av2_in, speaker_id=speaker.id)
    av3 = await crud.availability.create(db_tests, obj_in=av3_in, speaker_id=speaker.id)
    av4 = await crud.availability.create(db_tests, obj_in=av4_in, speaker_id=speaker.id)

    # tuesday
    s1 = await ut.create_random_session(db_tests, participant_id=db_data["p_1sw"].id,
                                        date_=dt.date(2022, 3, 24), time_=dt.time(9))
    s2 = await ut.create_random_session(db_tests, participant_id=db_data["p_1sw"].id,
                                        date_=dt.date(2022, 3, 24), time_=dt.time(10))
    # wednesday
    s3 = await ut.create_random_session(db_tests, participant_id=db_data["p_2sw"].id,
                                        date_=dt.date(2022, 4, 6), time_=dt.time(10))

    assert not await crud.speaker.get_free_sessions_times_by_date(db_tests, db_obj=db_data["speaker"],
                                                                  date=dt.date(2022, 4, 6))

    spk_free_times_list = await crud.speaker.get_free_sessions_times_by_date(db_tests, db_obj=db_data["speaker"],
                                                                             date=dt.date(2022, 3, 24))
    assert len(spk_free_times_list) == 1
    assert dt.time(14) in spk_free_times_list
    await crud.session.remove(db_tests, id=s1.id)
    await crud.session.remove(db_tests, id=s2.id)
    await crud.session.remove(db_tests, id=s3.id)
    await crud.availability.remove(db_tests, id=av1.id)
    await crud.availability.remove(db_tests, id=av2.id)
    await crud.availability.remove(db_tests, id=av3.id)
    await crud.availability.remove(db_tests, id=av4.id)
