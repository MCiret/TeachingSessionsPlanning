import datetime as dt

import pytest
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.schemas import SpeakerUpdate
from app.core.security import verify_password
from app.tests import utils as ut
from app.models import ParticipantType
from app.schemas import ParticipantTypeCreate, AvailabilityCreate, SessionCreate

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
    db_speaker = await crud.speaker.get_by_participant_id(db_tests, participant.id)
    assert db_speaker.id == speaker.id


@pytest.fixture
async def db_data(db_tests: AsyncSession) -> ParticipantType:
    """
    Database creation + yielding :
    1 speaker 30min slot_time
    + his 2 participants : one is 1 session week and 1 is 2 sessions week

    NB: every objects are removed from db at the end.
    """
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
    await crud.speaker.remove(db_tests, id=speaker.id)


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


@pytest.fixture
async def db_data2(db_tests: AsyncSession, db_data) -> ParticipantType:
    """
    Use speaker from db_data fixture for database creation + yielding availabilities :
    - 01/12/21 - 31/03/22 - tuesday - 9:00 + 9:30
    - 01/02/22 - 31/05/22 - tuesday - 10:00 + 10:30
    - 15/03/22 - 31/07/22 - tuesday - 14:00
    - 15/03/22 - 31/07/22 - wednesday - 10:00

    NB: every availabilities are removed from db at the end.
    """
    speaker = db_data["speaker"]
    av1_in = AvailabilityCreate(start_date=dt.date(2021, 12, 1),
                                end_date=dt.date(2022, 3, 31),
                                week_day=3,
                                time=dt.time(9))
    av1b_in = AvailabilityCreate(start_date=dt.date(2021, 12, 1),
                                end_date=dt.date(2022, 3, 31),
                                week_day=3,
                                time=dt.time(9, 30))
    av2_in = AvailabilityCreate(start_date=dt.date(2022, 2, 1),
                                end_date=dt.date(2022, 5, 31),
                                week_day=3,
                                time=dt.time(10))
    av2b_in = AvailabilityCreate(start_date=dt.date(2022, 2, 1),
                                end_date=dt.date(2022, 5, 31),
                                week_day=3,
                                time=dt.time(10, 30))
    av3_in = AvailabilityCreate(start_date=dt.date(2022, 3, 15),
                                end_date=dt.date(2022, 7, 31),
                                week_day=3,
                                time=dt.time(14))
    av4_in = AvailabilityCreate(start_date=dt.date(2022, 3, 15),
                                end_date=dt.date(2022, 7, 31),
                                week_day=2,
                                time=dt.time(10))
    av1 = await crud.availability.create(db_tests, obj_in=av1_in, speaker_id=speaker.id)
    av1b = await crud.availability.create(db_tests, obj_in=av1b_in, speaker_id=speaker.id)
    av2 = await crud.availability.create(db_tests, obj_in=av2_in, speaker_id=speaker.id)
    av2b = await crud.availability.create(db_tests, obj_in=av2b_in, speaker_id=speaker.id)
    av3 = await crud.availability.create(db_tests, obj_in=av3_in, speaker_id=speaker.id)
    av4 = await crud.availability.create(db_tests, obj_in=av4_in, speaker_id=speaker.id)
    yield
    await crud.availability.remove(db_tests, id=av1.id)
    await crud.availability.remove(db_tests, id=av1b.id)
    await crud.availability.remove(db_tests, id=av2.id)
    await crud.availability.remove(db_tests, id=av2b.id)
    await crud.availability.remove(db_tests, id=av3.id)
    await crud.availability.remove(db_tests, id=av4.id)


async def test_get_free_sessions_times_by_date(db_tests: AsyncSession, db_data, db_data2) -> None:
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
    assert len(spk_free_times_list) == 3
    assert (dt.time(9, 30) and dt.time(10, 30) and dt.time(14)) in spk_free_times_list
    await crud.session.remove(db_tests, id=s1.id)
    await crud.session.remove(db_tests, id=s2.id)
    await crud.session.remove(db_tests, id=s3.id)


async def test_is_free_for_session(db_tests: AsyncSession, db_data, db_data2) -> None:
    """
    Test if speaker has availability + no session...
    Speaker + his participants = created and get from db_data fixture
    + his availabilities => created by db_data2 fixture
    """
    speaker = db_data["speaker"]
    p_1sw_id = db_data["p_1sw"].id
    p_2sw_id = db_data["p_2sw"].id

    # Existing sessions :
    # tuesday 24/03/22 9:00 - 1 session week participant
    s1 = await ut.create_random_session(db_tests, participant_id=p_1sw_id,
                                        date_=dt.date(2022, 3, 24), time_=dt.time(9))
    # tuesday 24/03/22 10:30 - 1 session week participant
    s2 = await ut.create_random_session(db_tests, participant_id=p_1sw_id,
                                        date_=dt.date(2022, 3, 24), time_=dt.time(10, 30))
    # tuesday 17/02/22 9:00 + 9:30 - 2 sessions week participant
    s3 = await ut.create_random_session(db_tests, participant_id=p_2sw_id,
                                        date_=dt.date(2022, 2, 17), time_=dt.time(9))
    # tuesday 17/02/22 10:00 + 10:30 - 2 sessions week participant
    s4 = await ut.create_random_session(db_tests, participant_id=p_2sw_id,
                                        date_=dt.date(2022, 2, 17), time_=dt.time(10))
    # wednesday 06/04/22 10:00 - 1 session week participant
    s5 = await ut.create_random_session(db_tests, participant_id=p_1sw_id,
                                        date_=dt.date(2022, 4, 6), time_=dt.time(10))

    # Resume existing availabilities + sessions :
    # - 01/12/21 - 31/03/22 - tuesday - 9:00 + 9:30 <> 1 session 24/03/22 9:00 + 2 sessions 17/02/22 9:00 + 9:30
    # - 01/02/22 - 31/05/22 - tuesday - 10:00 + 10:30 <> 1 session 24/03/22 10:30 + 2 sessions 17/02/22 10:00 + 10:30
    # - 15/03/22 - 31/07/22 - tuesday - 14:00 <> 0 sessions
    # - 15/03/22 - 31/07/22 - wednesday - 10:00 <> 1 session 06/04/22 10:00

    # Sessions to test before creating... :
    # tuesday 18/11/21 9:00 - 1 session week participant => none availability...
    s_in = SessionCreate(date=dt.date(2021, 11, 18), time=dt.time(9), participant_id=p_1sw_id,
                          type_name="s_type_name", status_name="s_status_name")
    assert not await crud.speaker.is_free_for_session(db_tests, speaker, session_in=s_in)

    # tuesday 14/04/22 15:00 - 2 sessions week participant => none availability...
    s_in = SessionCreate(date=dt.date(2022, 4, 14), time=dt.time(15), participant_id=p_2sw_id,
                          type_name="s_type_name", status_name="s_status_name")
    assert not await crud.speaker.is_free_for_session(db_tests, speaker, session_in=s_in)

    # tuesday 10/02/22 9:00 - 1 session week participant => availability + no session
    s_in = SessionCreate(date=dt.date(2022, 2, 10), time=dt.time(9), participant_id=p_1sw_id,
                          type_name="s_type_name", status_name="s_status_name")
    assert await crud.speaker.is_free_for_session(db_tests, speaker, session_in=s_in)

    # tuesday 24/03/22 9:00 - 1 session week participant => availability but existing session
    s_in = SessionCreate(date=dt.date(2022, 3, 24), time=dt.time(9), participant_id=p_1sw_id,
                          type_name="s_type_name", status_name="s_status_name")
    assert not await crud.speaker.is_free_for_session(db_tests, speaker, session_in=s_in)

    # tuesday 17/02/22 9:30 - 1 session week participant => availability but existing session
    s_in = SessionCreate(date=dt.date(2022, 2, 17), time=dt.time(9, 30), participant_id=p_1sw_id,
                          type_name="s_type_name", status_name="s_status_name")
    assert not await crud.speaker.is_free_for_session(db_tests, speaker, session_in=s_in)

    # wednesday 11/05/22 10:00 - 2 sessions week participant => availability at 10:00 but not at 10:30
    s_in = SessionCreate(date=dt.date(2022, 5, 22), time=dt.time(10), participant_id=p_2sw_id,
                          type_name="s_type_name", status_name="s_status_name")
    assert not await crud.speaker.is_free_for_session(db_tests, speaker, session_in=s_in)

    # wednesday 06/04/22 9:30 - 2 sessions week participant
    # => no availability at 9:30, availability at 10:00 but existing session
    s_in = SessionCreate(date=dt.date(2022, 5, 22), time=dt.time(10), participant_id=p_2sw_id,
                          type_name="s_type_name", status_name="s_status_name")
    assert not await crud.speaker.is_free_for_session(db_tests, speaker, session_in=s_in)

    # tuesday 24/03/22 10:00 - 2 sessions week participant
    # => availability at 10:00 and 10:30 but existing session at 10:30
    s_in = SessionCreate(date=dt.date(2022, 3, 24), time=dt.time(10), participant_id=p_2sw_id,
                          type_name="s_type_name", status_name="s_status_name")
    assert not await crud.speaker.is_free_for_session(db_tests, speaker, session_in=s_in)

    # tuesday 26/05/22 10:00 - 2 sessions week participant => availability at 10:00 and at 10:30 + no session
    s_in = SessionCreate(date=dt.date(2022, 5, 26), time=dt.time(10), participant_id=p_2sw_id,
                          type_name="s_type_name", status_name="s_status_name")
    assert await crud.speaker.is_free_for_session(db_tests, speaker, session_in=s_in)

    await crud.session.remove(db_tests, id=s1.id)
    await crud.session.remove(db_tests, id=s2.id)
    await crud.session.remove(db_tests, id=s3.id)
    await crud.session.remove(db_tests, id=s4.id)
    await crud.session.remove(db_tests, id=s5.id)
