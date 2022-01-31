import datetime as dt

import pytest
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException


from app import crud
from app.core.config import settings
from app.schemas import SessionUpdate, SessionCreate
from app.schemas import Session as SessionSchema
from app.models import SessionType, SessionStatus
import app.tests.utils as ut

# This is the same as using the @pytest.mark.anyio on all test functions in the module
pytestmark = pytest.mark.anyio


async def test_create_session(db_tests: AsyncSession) -> None:
    date_ = dt.date.today()
    time_ = dt.datetime.now().time()
    participant = await ut.create_random_participant(db_tests)
    created_session = await ut.create_random_session(db_tests, date_=date_, time_=time_, participant_id=participant.id)
    db_created_session = await crud.session.get(db_tests, id=created_session.id)
    assert db_created_session.date == date_ and db_created_session.time == time_
    assert db_created_session.participant_id == participant.id
    assert hasattr(db_created_session, "comments")
    await crud.session.remove(db_tests, id=created_session.id)


async def test_get_session(db_tests: AsyncSession) -> None:
    created_session = await ut.create_random_session(db_tests)
    got_session = await crud.session.get(db_tests, id=created_session.id)
    assert got_session
    assert created_session.date == got_session.date\
        and created_session.time == got_session.time
    assert jsonable_encoder(got_session) == jsonable_encoder(created_session)
    await crud.session.remove(db_tests, id=created_session.id)


async def test_get_multi_session(db_tests: AsyncSession) -> None:
    s1 = await ut.create_random_session(db_tests)
    s2 = await ut.create_random_session(db_tests)
    s3 = await ut.create_random_session(db_tests)
    got_multi_session = await crud.session.get_multi(db_tests)
    assert len(got_multi_session) >= 3
    await crud.session.remove(db_tests, id=s1.id)
    await crud.session.remove(db_tests, id=s2.id)
    await crud.session.remove(db_tests, id=s3.id)


async def test_get_by_date_and_time(db_tests: AsyncSession) -> None:
    s_1a = await ut.create_random_session(db_tests, time_=dt.time(10, 30),
                                          date_=dt.date(2022, 1, 6))
    s_1b = await ut.create_random_session(db_tests, time_=dt.time(10, 30),
                                          date_=dt.date(2022, 1, 7))
    s_2a = await ut.create_random_session(db_tests, time_=dt.time(10, 30),
                                          date_=dt.date(2022, 1, 6))
    s_2b = await ut.create_random_session(db_tests, time_=dt.time(11, 30),
                                          date_=dt.date(2022, 1, 6))

    jan_6_10_30_sessions = await crud.session.get_by_date_and_time(db_tests, dt.date(2022, 1, 6),
                                                                             dt.time(10, 30))
    sessions_id_list = [session.id for session in jan_6_10_30_sessions]
    assert s_1a.id in sessions_id_list
    assert s_2a.id in sessions_id_list
    assert s_1b.id not in sessions_id_list
    assert s_2b.id not in sessions_id_list

    jan_7_11_30_sessions = await crud.session.get_by_date_and_time(db_tests, dt.date(2022, 1, 7),
                                                                             dt.time(11, 30))
    assert not jan_7_11_30_sessions

    jan_7_10_30_sessions = await crud.session.get_by_date_and_time(db_tests, dt.date(2022, 1, 7),
                                                                             dt.time(10, 30))
    sessions_id_list = [session.id for session in jan_7_10_30_sessions]
    assert s_1a.id not in sessions_id_list
    assert s_2a.id not in sessions_id_list
    assert s_1b.id in sessions_id_list
    assert s_2b.id not in sessions_id_list
    await crud.session.remove(db_tests, id=s_1a.id)
    await crud.session.remove(db_tests, id=s_1b.id)
    await crud.session.remove(db_tests, id=s_2a.id)
    await crud.session.remove(db_tests, id=s_2b.id)


async def test_get_by_date_speaker(db_tests: AsyncSession) -> None:
    speaker = await ut.create_random_speaker(db_tests)
    p1 = await ut.create_random_participant(db_tests, speaker_id=speaker.id)
    s_p1 = await ut.create_random_session(db_tests, date_=dt.date(2022, 1, 7), participant_id=p1.id)
    p2 = await ut.create_random_participant(db_tests, speaker_id=speaker.id)
    s1_p2 = await ut.create_random_session(db_tests, date_=dt.date(2022, 1, 7), participant_id=p2.id)
    s2_p2 = await ut.create_random_session(db_tests, date_=dt.date(2022, 1, 9), participant_id=p2.id)
    p3 = await ut.create_random_participant(db_tests)
    s_p3 = await ut.create_random_session(db_tests, date_=dt.date(2022, 1, 7), participant_id=p3.id)
    sessions = await crud.session.get_by_date_speaker(db_tests, dt.date(2022, 1, 7), speaker.id)
    session_ids = [s.id for s in sessions]
    assert (s_p1.id and s1_p2.id) in session_ids
    assert (s2_p2.id and s_p3.id) not in session_ids
    await crud.session.remove(db_tests, id=s_p1.id)
    await crud.session.remove(db_tests, id=s1_p2.id)
    await crud.session.remove(db_tests, id=s2_p2.id)
    await crud.session.remove(db_tests, id=s_p3.id)


async def test_update_session(db_tests: AsyncSession) -> None:
    created_session = await ut.create_random_session(db_tests)
    db_created_session = await crud.session.get(db_tests, id=created_session.id)
    new_time = dt.datetime.now().time()
    session_in_update = SessionUpdate(time=new_time)
    await crud.session.update(db_tests, db_obj=db_created_session, obj_in=session_in_update)
    updated_session = await crud.session.get(db_tests, id=db_created_session.id)
    assert updated_session
    assert created_session.date == updated_session.date
    assert created_session.id == updated_session.id
    await crud.session.remove(db_tests, id=created_session.id)


async def test_remove_session(db_tests: AsyncSession) -> None:
    created_session = await ut.create_random_session(db_tests)
    await crud.session.remove(db_tests, id=created_session.id)
    removed_session = await crud.session.get(db_tests, id=created_session.id)
    assert removed_session is None


async def test_from_db_model_to_schema_mocked_crud(db_tests: AsyncSession, mocker) -> None:
    session = await ut.create_random_session(db_tests)

    mock_get_type = mocker.patch('app.crud.session_type.get')
    mock_get_type.return_value = SessionType()
    mocker.patch.object(SessionType, 'name', "mock type name")
    mock_get_status = mocker.patch('app.crud.session_status.get')
    mock_get_status.return_value = SessionStatus()
    mocker.patch.object(SessionStatus, 'name', "mock status name")

    schema = await crud.session.from_db_model_to_schema(db_tests, session)

    assert mock_get_type.called
    assert mock_get_status.called
    assert schema.type_name == "mock type name"
    assert schema.status_name == "mock status name"
    assert isinstance(schema, SessionSchema)
    schema_dict = jsonable_encoder(schema)
    assert schema_dict["id"] == session.id
    assert schema_dict["type_name"] == "mock type name"
    assert schema_dict["status_name"] == "mock status name"
    await crud.session.remove(db_tests, id=session.id)


async def test_from_db_model_to_schema(db_tests: AsyncSession) -> None:
    session = await ut.create_random_session(db_tests)
    s_type_name = (await crud.session_type.get(db_tests, id=session.type_id)).name
    s_status_name = (await crud.session_status.get(db_tests, id=session.status_id)).name
    schema = await crud.session.from_db_model_to_schema(db_tests, session)
    assert schema.type_name == s_type_name
    assert schema.status_name == s_status_name
    assert isinstance(schema, SessionSchema)
    assert type(schema.date) == dt.date
    assert type(schema.time) == dt.time
    await crud.session.remove(db_tests, id=session.id)


async def test_from_schema_to_model_db_with_create_schema(db_tests: AsyncSession) -> None:
    participant = await ut.create_random_participant(db_tests)
    s_type_name = ut.random_list_elem(settings.SESSION_TYPES)
    s_status_name = ut.random_list_elem(settings.SESSION_STATUS)
    db_s_type = await crud.session_type.get_by_name(db_tests, s_type_name)
    db_s_status = await crud.session_status.get_by_name(db_tests, s_status_name)
    s_in = SessionCreate(date=dt.date.today(), time=dt.datetime.now().time(),
                         participant_id=participant.id, type_name=s_type_name, status_name=s_status_name)
    s_dict = await crud.session.from_schema_to_db_model(db_tests, obj_in=s_in)
    assert ("type_name" and "status_name") not in s_dict
    assert ("type_id" and "status_id" and "date" and "time") in s_dict
    assert s_dict["type_id"] == db_s_type.id
    assert s_dict["status_id"] == db_s_status.id
    assert s_dict["participant_id"] == participant.id
    assert type(s_dict["date"]) == dt.date
    assert type(s_dict["time"]) == dt.time


async def test_from_schema_to_model_db_with_update_schema_type_name(db_tests: AsyncSession) -> None:
    s_type_name = ut.random_list_elem(settings.SESSION_TYPES)
    db_s_type = await crud.session_type.get_by_name(db_tests, s_type_name)
    s_in = SessionUpdate(type_name=s_type_name)
    s_dict = await crud.session.from_schema_to_db_model(db_tests, obj_in=s_in)
    assert ("type_name" and "status_name" and "status_id" and "time" and "date") not in s_dict
    assert "type_id" in s_dict
    assert s_dict["type_id"] == db_s_type.id


async def test_from_schema_to_model_db_with_update_schema_date(db_tests: AsyncSession) -> None:
    date_ = dt.date.today()
    s_in = SessionUpdate(date=date_)
    s_dict = await crud.session.from_schema_to_db_model(db_tests, obj_in=s_in)
    assert ("type_name" and "status_name" and "type_id" and "time") not in s_dict
    assert "date" in s_dict
    assert s_dict["date"] == date_
    assert type(s_dict["date"]) == dt.date


async def test_from_schema_to_model_db_with_update_schema(db_tests: AsyncSession) -> None:
    s_type_name = ut.random_list_elem(settings.SESSION_TYPES)
    s_status_name = ut.random_list_elem(settings.SESSION_STATUS)
    date_ = dt.date.today()
    time_ = dt.datetime.now().time()
    db_s_type = await crud.session_type.get_by_name(db_tests, s_type_name)
    db_s_status = await crud.session_status.get_by_name(db_tests, s_status_name)
    s_in = SessionUpdate(type_name=s_type_name, status_name=s_status_name, date=date_, time=time_)
    s_dict = await crud.session.from_schema_to_db_model(db_tests, obj_in=s_in)
    assert ("type_name" and "status_name") not in s_dict
    assert ("type_id" and "status_id" and "date" and "time") in s_dict
    assert s_dict["type_id"] == db_s_type.id
    assert s_dict["status_id"] == db_s_status.id
    assert s_dict["date"] == date_
    assert type(s_dict["date"]) == dt.date
    assert s_dict["time"] == time_
    assert type(s_dict["time"]) == dt.time


async def test_get_by_participant_email(db_tests: AsyncSession) -> None:
    p1 = await ut.create_random_participant(db_tests)
    s1_p1 = await ut.create_random_session(db_tests, participant_id=p1.id)
    s2_p1 = await ut.create_random_session(db_tests, participant_id=p1.id)
    p2 = await ut.create_random_participant(db_tests)
    s_p2 = await ut.create_random_session(db_tests, participant_id=p2.id)

    p1_sessions = await crud.session.get_by_participant_email(db_tests, p1.email)
    p1_sessions_id = [session.id for session in p1_sessions]
    assert (s1_p1.id and s2_p1.id) in p1_sessions_id
    assert s_p2.id not in p1_sessions_id
    await crud.session.remove(db_tests, id=s1_p1.id)
    await crud.session.remove(db_tests, id=s2_p1.id)
    await crud.session.remove(db_tests, id=s_p2.id)


async def test_get_by_speaker_email(db_tests: AsyncSession) -> None:
    speaker1 = await ut.create_random_speaker(db_tests)
    p1_id = (await ut.create_random_participant(db_tests, speaker_id=speaker1.id)).id
    p2_id = (await ut.create_random_participant(db_tests, speaker_id=speaker1.id)).id
    p3_id = (await ut.create_random_participant(db_tests, speaker_id=speaker1.id)).id
    s_p1 = await ut.create_random_session(db_tests, participant_id=p1_id)
    s_p2 = await ut.create_random_session(db_tests, participant_id=p2_id)
    s_p3 = await ut.create_random_session(db_tests, participant_id=p3_id)
    speaker2 = await ut.create_random_speaker(db_tests)
    p4_id = (await ut.create_random_participant(db_tests, speaker_id=speaker2.id)).id
    s_p4 = await ut.create_random_session(db_tests, participant_id=p4_id)

    # get speaker1 sessions
    speaker1_sessions_by_email = await crud.session.get_by_speaker_email(db_tests, speaker1.email)
    sessions_id = [session.id for session in speaker1_sessions_by_email]
    assert (s_p1.id and s_p2.id and s_p3.id) in sessions_id
    # assert speaker2 session was not selected
    assert s_p4 not in sessions_id
    await crud.session.remove(db_tests, id=s_p1.id)
    await crud.session.remove(db_tests, id=s_p2.id)
    await crud.session.remove(db_tests, id=s_p3.id)
    await crud.session.remove(db_tests, id=s_p4.id)


async def test_participant_checks_and_get_id_current_user_participant(db_tests: AsyncSession) -> None:
    session_in = SessionCreate(date=dt.date.today(), time=dt.datetime.now().time(),
                               participant_id=None, type_name="type name", status_name="status name")
    participant = await ut.create_random_participant(db_tests)
    assert await crud.session\
                     .participant_checks_and_get_id(db_tests, session_in, current_user=participant) == participant.id


async def test_participant_checks_and_get_id_current_user_speaker(db_tests: AsyncSession) -> None:
    speaker = await ut.create_random_speaker(db_tests)
    participant = await ut.create_random_participant(db_tests, speaker_id=speaker.id)
    session_in = SessionCreate(date=dt.date.today(), time=dt.datetime.now().time(),
                               participant_id=participant.id, type_name="type name", status_name="status name")
    assert await crud.session.participant_checks_and_get_id(db_tests, session_in,
                                                            current_user=speaker) == participant.id


async def test_participant_checks_and_get_id_current_user_speaker_participant_id_none(db_tests: AsyncSession
                                                                                      ) -> None:
    session_in = SessionCreate(date=dt.date.today(), time=dt.datetime.now().time(),
                               participant_id=None, type_name="type name", status_name="status name")
    speaker = await ut.create_random_speaker(db_tests)
    with pytest.raises(HTTPException) as he:
        await crud.session.participant_checks_and_get_id(db_tests, session_in, current_user=speaker)
    assert "If you are not a Participant user, you have to set the participant_id value..." in str(he)


async def test_participant_checks_and_get_id_current_user_speaker_participant_id_not_exist(db_tests: AsyncSession,
                                                                                           mocker) -> None:
    session_in = SessionCreate(date=dt.date.today(), time=dt.datetime.now().time(),
                               participant_id=1, type_name="type name", status_name="status name")
    mock_get_participant = mocker.patch('app.crud.participant.get')
    mock_get_participant.return_value = False
    speaker = await ut.create_random_speaker(db_tests)
    with pytest.raises(HTTPException) as he:
        await crud.session.participant_checks_and_get_id(db_tests, session_in, current_user=speaker)
    assert "A participant user with this id does not exist in the system..." in str(he)
    assert mock_get_participant.called


async def test_participant_checks_and_get_id_current_user_speaker_not_his_participant(db_tests: AsyncSession
                                                                                      ) -> None:
    speaker = await ut.create_random_speaker(db_tests)
    not_speaker_participant = await ut.create_random_participant(db_tests)
    session_in = SessionCreate(date=dt.date.today(), time=dt.datetime.now().time(),
                               participant_id=not_speaker_participant.id,
                               type_name="type name", status_name="status name")
    with pytest.raises(HTTPException) as he:
        await crud.session.participant_checks_and_get_id(db_tests, session_in, current_user=speaker)
    assert "The participant with this id is not one of yours..." in str(he)


async def test_type_and_status_names_checks(db_tests: AsyncSession, mocker) -> None:
    session_in = SessionUpdate(type_name="some type", status_name="some status")
    mocker_type_get_by_name = mocker.patch('app.crud.session_type.get_by_name')
    mocker_type_get_by_name.return_value = True
    mocker_status_get_by_name = mocker.patch('app.crud.session_status.get_by_name')
    mocker_status_get_by_name.return_value = True
    # assert None is returned (and so no exception was raised)
    assert await crud.session.type_and_status_names_checks(db_tests, session_in) is None


async def test_type_and_status_names_checks_type_and_status_not_set(db_tests: AsyncSession) -> None:
    """When updating a Session, type and status names fields could not be set."""
    session_in = SessionUpdate()
    assert await crud.session.type_and_status_names_checks(db_tests, session_in) is None


async def test_type_and_status_names_checks_type_not_existing(db_tests: AsyncSession, mocker) -> None:
    session_in = SessionUpdate(type_name="some type", status_name="some status")
    mocker_type_get_by_name = mocker.patch('app.crud.session_type.get_by_name')
    mocker_type_get_by_name.return_value = False
    mocker_status_get_by_name = mocker.patch('app.crud.session_status.get_by_name')
    mocker_status_get_by_name.return_value = True
    with pytest.raises(HTTPException) as he:
        await crud.session.type_and_status_names_checks(db_tests, session_in)
    assert f"Type {session_in.type_name} does not exists..." in str(he)


async def test_type_and_status_names_checks_status_not_existing(db_tests: AsyncSession, mocker) -> None:
    session_in = SessionUpdate(type_name="some type", status_name="some status")
    mocker_type_get_by_name = mocker.patch('app.crud.session_type.get_by_name')
    mocker_type_get_by_name.return_value = True
    mocker_status_get_by_name = mocker.patch('app.crud.session_status.get_by_name')
    mocker_status_get_by_name.return_value = False
    with pytest.raises(HTTPException) as he:
        await crud.session.type_and_status_names_checks(db_tests, session_in)
    assert f"Status {session_in.status_name} does not exists..." in str(he)


# async def test_get_speaker(db_tests: AsyncSession) -> None:
#     participant = await ut.create_random_participant(db_tests)
#     session = await ut.create_random_session(db_tests, participant_id=participant.id)
#     speaker = await crud.session.get_speaker(db_tests, db_obj=session)
#     assert speaker.id == participant.speaker_id
#     await crud.session.remove(db_tests, id=session.id)


# async def test_is_start_time_free_true_not_existing_session(db_tests: AsyncSession) -> None:
#     speaker = await ut.create_random_speaker(db_tests)
#     participant = await ut.create_random_participant(db_tests, speaker_id=speaker.id)
#     # another session with same time + date but random participant and so random speaker :
#     s1 = await ut.create_random_session(db_tests, time_=dt.time(10, 30), date_=dt.date(2022, 1, 20))
#     # create a same time but different date session :
#     s2 = await ut.create_random_session(db_tests, time_=dt.time(10, 30), date_=dt.date(2022, 1, 19),
#                                         participant_id=participant.id)
#     session_in = SessionCreate(date=dt.date(2022, 1, 20), time=dt.time(10, 30),
#                                participant_id=participant.id,
#                                type_name="type name", status_name="status name")
#     assert await crud.session.is_start_time_free(db_tests, obj_in=session_in)
#     await crud.session.remove(db_tests, id=s1.id)
#     await crud.session.remove(db_tests, id=s2.id)


# async def test_is_start_time_free_false_existing_identical_session(db_tests: AsyncSession) -> None:
#     """NB: identical session means same time + date + speaker."""
#     speaker = await ut.create_random_speaker(db_tests)
#     p1 = await ut.create_random_participant(db_tests, speaker_id=speaker.id)
#     s1 = await ut.create_random_session(db_tests, time_=dt.time(10, 30), date_=dt.date(2022, 1, 20),
#                                         participant_id=p1.id)
#     # another session with same time + date but random participant and so random speaker :
#     s2 = await ut.create_random_session(db_tests, time_=dt.time(10, 30), date_=dt.date(2022, 1, 20))

#     p2 = await ut.create_random_participant(db_tests, speaker_id=speaker.id)
#     session_in_p2 = SessionCreate(date=dt.date(2022, 1, 20), time=dt.time(10, 30),
#                                   participant_id=p2.id, type_name="type name", status_name="status name")
#     assert not await crud.session.is_start_time_free(db_tests, obj_in=session_in_p2)
#     await crud.session.remove(db_tests, id=s1.id)
#     await crud.session.remove(db_tests, id=s2.id)


# async def test_is_start_time_free_false_existing_two_slots_time_session_one_slot_time_before(db_tests: AsyncSession
#                                                                                              ) -> None:
#     speaker = await ut.create_random_speaker(db_tests, slot_time=30)
#     p_type_two_sessions_week = await crud.participant_type\
#                                          .create(db_tests, obj_in={"name": "p type name", "nb_session_week": 2})
#     p1 = await ut.create_random_participant(db_tests, speaker_id=speaker.id, p_type_name=p_type_two_sessions_week.name)
#     s1_p1 = await ut.create_random_session(db_tests, time_=dt.time(10, 00), date_=dt.date(2022, 1, 20),
#                                            participant_id=p1.id)
#     # another session with same time + date but random participant and so random speaker :
#     s2 = await ut.create_random_session(db_tests, time_=dt.time(10, 30), date_=dt.date(2022, 1, 20))

#     p2 = await ut.create_random_participant(db_tests, speaker_id=speaker.id)
#     session_in_p2 = SessionCreate(date=dt.date(2022, 1, 20), time=dt.time(10, 30),
#                                   participant_id=p2.id, type_name="type name", status_name="status name")
#     assert not await crud.session.is_start_time_free(db_tests, obj_in=session_in_p2)

#     await crud.session.remove(db_tests, id=s1_p1.id)
#     await crud.session.remove(db_tests, id=s2.id)
#     await crud.participant.remove(db_tests, id=p1.id)
#     await crud.participant_type.remove(db_tests, id=p_type_two_sessions_week.id)


# async def test_is_start_time_free_true_existing_two_slots_time_session_two_slots_time_before(db_tests: AsyncSession
#                                                                                              ) -> None:
#     speaker = await ut.create_random_speaker(db_tests, slot_time=30)
#     p_type_two_sessions_week = await crud.participant_type\
#                                          .create(db_tests, obj_in={"name": "p type name", "nb_session_week": 2})
#     p1 = await ut.create_random_participant(db_tests, speaker_id=speaker.id, p_type_name=p_type_two_sessions_week.name)
#     s1_p1 = await ut.create_random_session(db_tests, time_=dt.time(9, 30), date_=dt.date(2022, 1, 20),
#                                            participant_id=p1.id)
#     # another session with same time + date but random participant and so random speaker :
#     s2 = await ut.create_random_session(db_tests, time_=dt.time(10, 30), date_=dt.date(2022, 1, 20))

#     p2 = await ut.create_random_participant(db_tests, speaker_id=speaker.id)
#     session_in_p2 = SessionCreate(date=dt.date(2022, 1, 20), time=dt.time(10, 30),
#                                   participant_id=p2.id, type_name="type name", status_name="status name")
#     assert await crud.session.is_start_time_free(db_tests, obj_in=session_in_p2)

#     await crud.session.remove(db_tests, id=s1_p1.id)
#     await crud.session.remove(db_tests, id=s2.id)
#     await crud.participant.remove(db_tests, id=p1.id)
#     await crud.participant_type.remove(db_tests, id=p_type_two_sessions_week.id)


# async def test_is_start_time_free_false_existing_3_slots_time_session_two_slots_time_before(db_tests: AsyncSession
#                                                                                             ) -> None:
#     speaker = await ut.create_random_speaker(db_tests, slot_time=30)
#     p_type_3_sessions_week = await crud.participant_type\
#                                        .create(db_tests, obj_in={"name": "p type name", "nb_session_week": 3})
#     p1 = await ut.create_random_participant(db_tests, speaker_id=speaker.id,
#                                             p_type_name=p_type_3_sessions_week.name)
#     s1_p1 = await ut.create_random_session(db_tests, time_=dt.time(9, 30), date_=dt.date(2022, 1, 20),
#                                            participant_id=p1.id)
#     # another session with same time + date but random participant and so random speaker :
#     s2 = await ut.create_random_session(db_tests, time_=dt.time(10, 30), date_=dt.date(2022, 1, 20))

#     p2 = await ut.create_random_participant(db_tests, speaker_id=speaker.id)
#     session_in_p2 = SessionCreate(date=dt.date(2022, 1, 20), time=dt.time(10, 30),
#                                   participant_id=p2.id, type_name="type name", status_name="status name")
#     assert not await crud.session.is_start_time_free(db_tests, obj_in=session_in_p2)

#     await crud.session.remove(db_tests, id=s1_p1.id)
#     await crud.session.remove(db_tests, id=s2.id)
#     await crud.participant.remove(db_tests, id=p1.id)
#     await crud.participant_type.remove(db_tests, id=p_type_3_sessions_week.id)


# async def test_is_start_time_free_true_existing_3_slots_time_session_3_slots_time_before(db_tests: AsyncSession
#                                                                                          ) -> None:
#     speaker = await ut.create_random_speaker(db_tests, slot_time=30)
#     p_type_3_sessions_week = await crud.participant_type\
#                                        .create(db_tests, obj_in={"name": "p type name", "nb_session_week": 3})
#     p1 = await ut.create_random_participant(db_tests, speaker_id=speaker.id, p_type_name=p_type_3_sessions_week.name)
#     s1_p1 = await ut.create_random_session(db_tests, time_=dt.time(9, 00), date_=dt.date(2022, 1, 20),
#                                            participant_id=p1.id)
#     # another session with same time + date but random participant and so random speaker :
#     s2 = await ut.create_random_session(db_tests, time_=dt.time(10, 30), date_=dt.date(2022, 1, 20))

#     p2 = await ut.create_random_participant(db_tests, speaker_id=speaker.id)
#     session_in_p2 = SessionCreate(date=dt.date(2022, 1, 20), time=dt.time(10, 30),
#                                   participant_id=p2.id, type_name="type name", status_name="status name")
#     assert await crud.session.is_start_time_free(db_tests, obj_in=session_in_p2)

#     await crud.session.remove(db_tests, id=s1_p1.id)
#     await crud.session.remove(db_tests, id=s2.id)
#     await crud.participant.remove(db_tests, id=p1.id)
#     await crud.participant_type.remove(db_tests, id=p_type_3_sessions_week.id)


# async def test_is_slot_time_free_until_end_true_not_existing_session(db_tests: AsyncSession) -> None:
#     speaker = await ut.create_random_speaker(db_tests)
#     participant = await ut.create_random_participant(db_tests, speaker_id=speaker.id)
#     # create a same time but different date session :
#     s1 = await ut.create_random_session(db_tests, time_=dt.time(10, 30), date_=dt.date(2022, 1, 19),
#                                         participant_id=participant.id)
#     # another session with same time + date but random participant and so random speaker :
#     s2 = await ut.create_random_session(db_tests, time_=dt.time(10, 30), date_=dt.date(2022, 1, 20))

#     session_in = SessionCreate(date=dt.date(2022, 1, 20), time=dt.time(10, 30),
#                                participant_id=participant.id,
#                                type_name="type name", status_name="status name")
#     assert await crud.session.is_slot_time_free_until_end(db_tests, obj_in=session_in)
#     await crud.session.remove(db_tests, id=s1.id)
#     await crud.session.remove(db_tests, id=s2.id)


# async def test_is_slot_time_free_until_end_false_existing_identical_session(db_tests: AsyncSession) -> None:
#     """NB: identical session means same time + date + speaker."""
#     speaker = await ut.create_random_speaker(db_tests)
#     p1 = await ut.create_random_participant(db_tests, speaker_id=speaker.id)
#     s1 = await ut.create_random_session(db_tests, time_=dt.time(10, 30), date_=dt.date(2022, 1, 20),
#                                         participant_id=p1.id)
#     # another session with same time + date but random participant and so random speaker :
#     s2 = await ut.create_random_session(db_tests, time_=dt.time(10, 30), date_=dt.date(2022, 1, 20))

#     p2 = await ut.create_random_participant(db_tests, speaker_id=speaker.id)
#     session_in_p2 = SessionCreate(date=dt.date(2022, 1, 20), time=dt.time(10, 30),
#                                   participant_id=p2.id, type_name="type name", status_name="status name")
#     assert not await crud.session.is_slot_time_free_until_end(db_tests, obj_in=session_in_p2)
#     await crud.session.remove(db_tests, id=s1.id)
#     await crud.session.remove(db_tests, id=s2.id)


# async def test_is_slot_time_free_until_end_false_2_slots_existing_session_1_slot_after(db_tests: AsyncSession) -> None:
#     speaker = await ut.create_random_speaker(db_tests, slot_time=45)
#     p1 = await ut.create_random_participant(db_tests, speaker_id=speaker.id)
#     s1 = await ut.create_random_session(db_tests, time_=dt.time(11, 00), date_=dt.date(2022, 1, 20),
#                                         participant_id=p1.id)
#     # another session with same time + date but random participant and so random speaker :
#     s2 = await ut.create_random_session(db_tests, time_=dt.time(10, 30), date_=dt.date(2022, 1, 20))

#     p_type_two_sessions_week = await crud.participant_type\
#                                          .create(db_tests, obj_in={"name": "type_name", "nb_session_week": 2})
#     p2 = await ut.create_random_participant(db_tests, speaker_id=speaker.id, p_type_name=p_type_two_sessions_week.name)
#     session_in_p2 = SessionCreate(date=dt.date(2022, 1, 20), time=dt.time(10, 15),
#                                   participant_id=p2.id, type_name="type name", status_name="status name")
#     assert not await crud.session.is_slot_time_free_until_end(db_tests, obj_in=session_in_p2)

#     await crud.session.remove(db_tests, id=s1.id)
#     await crud.session.remove(db_tests, id=s2.id)
#     await crud.participant.remove(db_tests, id=p2.id)
#     await crud.participant_type.remove(db_tests, id=p_type_two_sessions_week.id)


# async def test_is_slot_time_free_until_end_true_2_slots_existing_session_2_slots_after(db_tests: AsyncSession) -> None:
#     speaker = await ut.create_random_speaker(db_tests, slot_time=30)
#     p1 = await ut.create_random_participant(db_tests, speaker_id=speaker.id)
#     s1 = await ut.create_random_session(db_tests, time_=dt.time(11, 30), date_=dt.date(2022, 1, 20),
#                                         participant_id=p1.id)
#     # another session with same time + date but random participant and so random speaker :
#     s2 = await ut.create_random_session(db_tests, time_=dt.time(10, 30), date_=dt.date(2022, 1, 20))

#     p_type_two_sessions_week = await crud.participant_type\
#                                          .create(db_tests, obj_in={"name": "type_name", "nb_session_week": 2})
#     p2 = await ut.create_random_participant(db_tests, speaker_id=speaker.id, p_type_name=p_type_two_sessions_week.name)
#     session_in_p2 = SessionCreate(date=dt.date(2022, 1, 20), time=dt.time(10, 30),
#                                   participant_id=p2.id, type_name="type name", status_name="status name")
#     assert await crud.session.is_slot_time_free_until_end(db_tests, obj_in=session_in_p2)
#     await crud.session.remove(db_tests, id=s1.id)
#     await crud.session.remove(db_tests, id=s2.id)
#     await crud.participant.remove(db_tests, id=p2.id)
#     await crud.participant_type.remove(db_tests, id=p_type_two_sessions_week.id)


class TestIsWholeSlotTimeFree:
    @pytest.fixture
    async def mocks_crud(self, request, mocker):
        mock_is_start_time = mocker.patch('app.crud.session.is_start_time_free')
        mock_is_start_time.return_value = request.node.get_closest_marker("start_time").args[0]
        # return mock_is_start_time
        mock_is_free_until_end = mocker.patch('app.crud.session.is_slot_time_free_until_end')
        mock_is_free_until_end.return_value = request.node.get_closest_marker("until_end").args[0]
        return {"mock_is_start_time": mock_is_start_time,
                "mock_is_free_until_end": mock_is_free_until_end}

    session_in = SessionCreate(date=dt.date(2022, 1, 20), time=dt.time(10, 30),
                               participant_id=1, type_name="type name", status_name="status name")

    @pytest.mark.until_end(True)
    @pytest.mark.start_time(True)
    async def test_is_whole_slot_time_free_true(self, db_tests: AsyncSession, mocks_crud) -> None:
        assert await crud.session.is_whole_slot_time_free(db_tests, obj_in=self.session_in)
        for m in mocks_crud:
            assert mocks_crud[m].called

    @pytest.mark.until_end(True)
    @pytest.mark.start_time(False)
    async def test_is_whole_slot_time_free_false_start_time_false(self, db_tests: AsyncSession, mocks_crud) -> None:
        assert not await crud.session.is_whole_slot_time_free(db_tests, obj_in=self.session_in)
        assert mocks_crud["mock_is_start_time"].called
        assert not mocks_crud["mock_is_free_until_end"].called

    @pytest.mark.until_end(False)
    @pytest.mark.start_time(True)
    async def test_is_whole_slot_time_free_false_time_until_end_false(self, db_tests: AsyncSession,
                                                                      mocks_crud) -> None:
        assert not await crud.session.is_whole_slot_time_free(db_tests, obj_in=self.session_in)
        assert mocks_crud["mock_is_start_time"].called
        assert mocks_crud["mock_is_free_until_end"].called

    @pytest.mark.until_end(False)
    @pytest.mark.start_time(False)
    async def test_is_whole_slot_time_free_false_both_false(self, db_tests: AsyncSession, mocks_crud) -> None:
        assert not await crud.session.is_whole_slot_time_free(db_tests, obj_in=self.session_in)
        assert mocks_crud["mock_is_start_time"].called
        assert not mocks_crud["mock_is_free_until_end"].called
