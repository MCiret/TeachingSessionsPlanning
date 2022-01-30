import pytest
from fastapi.encoders import jsonable_encoder
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.core.config import settings
from app.schemas import ParticipantUpdate, ParticipantCreate
from app.schemas import Participant as ParticipantSchema
from app.models import ParticipantType, ParticipantStatus
from app.core.security import verify_password
from app.tests import utils as ut

# This is the same as using the @pytest.mark.anyio on all test functions in the module
pytestmark = pytest.mark.anyio


async def test_create_participant(db_tests: AsyncSession) -> None:
    email = ut.random_email()
    created_participant = await ut.create_random_participant(db_tests, email=email)
    got_participant = await crud.participant.get(db_tests, id=created_participant.id)
    assert got_participant.email == email
    assert got_participant.profile == "participant"
    assert hasattr(got_participant, "hashed_api_key")


async def test_get_participant(db_tests: AsyncSession) -> None:
    created_participant = await ut.create_random_participant(db_tests)
    got_participant = await crud.participant.get(db_tests, id=created_participant.id)
    assert got_participant
    assert got_participant.profile == "participant"
    assert created_participant.email == got_participant.email
    assert jsonable_encoder(got_participant) == jsonable_encoder(created_participant)


async def test_get_multi_participant(db_tests: AsyncSession) -> None:
    await ut.create_random_participant(db_tests)
    await ut.create_random_participant(db_tests)
    await ut.create_random_participant(db_tests)
    got_multi_participant = await crud.participant.get_multi(db_tests)
    assert len(got_multi_participant) >= 3


async def test_update_participant(db_tests: AsyncSession) -> None:
    participant = await ut.create_random_participant(db_tests)
    new_api_key = ut.random_lower_string(32)
    participant_in = ParticipantUpdate(api_key=new_api_key)
    await crud.participant.update(db_tests, db_obj=participant, obj_in=participant_in)
    updated_participant = await crud.participant.get(db_tests, id=participant.id)
    assert updated_participant
    assert participant.email == updated_participant.email
    assert verify_password(new_api_key, updated_participant.hashed_api_key)


async def test_remove_participant(db_tests: AsyncSession) -> None:
    created_participant = await ut.create_random_participant(db_tests)
    await crud.participant.remove(db_tests, id=created_participant.id)
    removed_participant = await crud.participant.get(db_tests, id=created_participant.id)
    assert removed_participant is None


async def test_speaker_checks_and_get_id_current_user_is_speaker(db_tests: AsyncSession) -> None:
    participant_in = ParticipantCreate(
        email=ut.random_email(), type_name="type name", status_name="status name",
        speaker_id=None, api_key=ut.random_lower_string(32), first_name=ut.random_lower_string(6),
        last_name=ut.random_lower_string(6))
    speaker = await ut.create_random_speaker(db_tests)
    assert await crud.participant.speaker_checks_and_get_id(db_tests, participant_in,
                                                            current_user=speaker) == speaker.id


async def test_speaker_checks_and_get_id_current_user_is_admin(db_tests: AsyncSession) -> None:
    admin = await ut.create_random_admin(db_tests)
    speaker = await ut.create_random_speaker(db_tests)
    participant_in = ParticipantCreate(
        email=ut.random_email(), type_name="type name", status_name="status name",
        speaker_id=speaker.id, api_key=ut.random_lower_string(32), first_name=ut.random_lower_string(6),
        last_name=ut.random_lower_string(6))
    assert await crud.participant.speaker_checks_and_get_id(db_tests, participant_in, current_user=admin) == speaker.id


async def test_before_create_update_spk_checks_and_get_id_curr_user_admin_speaker_id_none(db_tests: AsyncSession
                                                                                          ) -> None:
    participant_in = ParticipantCreate(
        email=ut.random_email(), type_name="type name", status_name="status name",
        speaker_id=None, api_key=ut.random_lower_string(32), first_name=ut.random_lower_string(6),
        last_name=ut.random_lower_string(6))
    admin = await ut.create_random_admin(db_tests)
    with pytest.raises(HTTPException) as he:
        await crud.participant.speaker_checks_and_get_id(db_tests, participant_in, current_user=admin)
    assert "If you are not a Speaker user, you have to set the speaker_id value..." in str(he)


async def test_before_create_update_spk_checks_and_get_id_curr_user_admin_speaker_id_not_exist(db_tests: AsyncSession,
                                                                                               mocker) -> None:
    participant_in = ParticipantCreate(
        email=ut.random_email(), type_name="type name", status_name="status name",
        speaker_id=1, api_key=ut.random_lower_string(32), first_name=ut.random_lower_string(6),
        last_name=ut.random_lower_string(6))
    mock_get_speaker = mocker.patch('app.crud.speaker.get')
    mock_get_speaker.return_value = False
    admin = await ut.create_random_admin(db_tests)
    with pytest.raises(HTTPException) as he:
        await crud.participant.speaker_checks_and_get_id(db_tests, participant_in, current_user=admin)
    assert "A speaker user with this id does not exist in the system..." in str(he)
    assert mock_get_speaker.called


async def test_type_and_status_names_checks(db_tests: AsyncSession, mocker) -> None:
    participant_in = ParticipantUpdate(type_name="some type", status_name="some status")
    mocker_type_get_by_name = mocker.patch('app.crud.participant_type.get_by_name')
    mocker_type_get_by_name.return_value = True
    mocker_status_get_by_name = mocker.patch('app.crud.participant_status.get_by_name')
    mocker_status_get_by_name.return_value = True
    # assert None is returned (and so no exception was raised)
    assert await crud.participant.type_and_status_names_checks(db_tests, participant_in) is None


async def test_type_status_names_checks_type_and_status_not_set(db_tests: AsyncSession) -> None:
    """When updating a Participant, type and status names fields could not be set."""
    participant_in = ParticipantUpdate()
    assert await crud.participant.type_and_status_names_checks(db_tests, participant_in) is None


async def test_type_status_names_checks_type_not_existing(db_tests: AsyncSession, mocker) -> None:
    participant_in = ParticipantUpdate(type_name="some type", status_name="some status")
    mocker_type_get_by_name = mocker.patch('app.crud.participant_type.get_by_name')
    mocker_type_get_by_name.return_value = False
    mocker_status_get_by_name = mocker.patch('app.crud.participant_status.get_by_name')
    mocker_status_get_by_name.return_value = True
    with pytest.raises(HTTPException) as he:
        await crud.participant.type_and_status_names_checks(db_tests, participant_in)
    assert f"Type {participant_in.type_name} does not exists..." in str(he)


async def test_type_status_names_checks_status_not_exist(db_tests: AsyncSession, mocker) -> None:
    participant_in = ParticipantUpdate(type_name="some type", status_name="some status")
    mocker_type_get_by_name = mocker.patch('app.crud.participant_type.get_by_name')
    mocker_type_get_by_name.return_value = True
    mocker_status_get_by_name = mocker.patch('app.crud.participant_status.get_by_name')
    mocker_status_get_by_name.return_value = False
    with pytest.raises(HTTPException) as he:
        await crud.participant.type_and_status_names_checks(db_tests, participant_in)
    assert f"Status {participant_in.status_name} does not exists..." in str(he)


async def test_from_db_model_to_schema_mocked_crud(db_tests: AsyncSession, mocker) -> None:
    participant = await ut.create_random_participant(db_tests)

    mock_get_type = mocker.patch('app.crud.participant_type.get')
    mock_get_type.return_value = ParticipantType()
    mocker.patch.object(ParticipantType, 'name', "mock type name")
    mock_get_status = mocker.patch('app.crud.participant_status.get')
    mock_get_status.return_value = ParticipantStatus()
    mocker.patch.object(ParticipantStatus, 'name', "mock status name")

    schema = await crud.participant.from_db_model_to_schema(db_tests, participant)

    assert mock_get_type.called
    assert mock_get_status.called
    assert schema.type_name == "mock type name"
    assert schema.status_name == "mock status name"
    assert isinstance(schema, ParticipantSchema)
    schema_dict = jsonable_encoder(schema)
    assert schema_dict["email"] == participant.email
    assert schema_dict["type_name"] == "mock type name"
    assert schema_dict["status_name"] == "mock status name"


async def test_from_db_model_to_schema(db_tests: AsyncSession) -> None:
    # create a participant and get its type and status names :
    participant = await ut.create_random_participant(db_tests)
    p_type_name = (await crud.participant_type.get(db_tests, id=participant.type_id)).name
    p_status_name = (await crud.participant_status.get(db_tests, id=participant.status_id)).name

    schema = await crud.participant.from_db_model_to_schema(db_tests, participant)
    assert schema.type_name == p_type_name
    assert schema.status_name == p_status_name
    assert isinstance(schema, ParticipantSchema)
    schema_dict = jsonable_encoder(schema)
    assert schema_dict["email"] == participant.email
    assert schema_dict["type_name"] == p_type_name
    assert schema_dict["status_name"] == p_status_name


async def test_from_schema_to_model_db_with_create_schema(db_tests: AsyncSession) -> None:
    speaker = await ut.create_random_speaker(db_tests)
    p_type_name = ut.random_list_elem(list(settings.PARTICIPANT_TYPES_NB_SESSION_WEEK.keys()))
    p_status_name = ut.random_list_elem(settings.PARTICIPANT_STATUS)
    db_p_type = await crud.participant_type.get_by_name(db_tests, p_type_name)
    db_p_status = await crud.participant_status.get_by_name(db_tests, p_status_name)
    p_in = ParticipantCreate(
        email=ut.random_email(), type_name=p_type_name, status_name=p_status_name,
        speaker_id=speaker.id, api_key=ut.random_lower_string(32), first_name=ut.random_lower_string(6),
        last_name=ut.random_lower_string(6))
    p_dict = await crud.participant.from_schema_to_db_model(db_tests, obj_in=p_in)
    assert ("type_name" and "status_name") not in p_dict
    assert ("type_id" and "status_id") in p_dict
    assert p_dict["type_id"] == db_p_type.id
    assert p_dict["status_id"] == db_p_status.id
    assert p_dict["speaker_id"] == speaker.id


async def test_from_schema_to_model_db_with_update_schema_type_name(db_tests: AsyncSession) -> None:
    p_type_name = ut.random_list_elem(list(settings.PARTICIPANT_TYPES_NB_SESSION_WEEK.keys()))
    db_p_type = await crud.participant_type.get_by_name(db_tests, p_type_name)
    p_in = ParticipantUpdate(type_name=p_type_name)
    p_dict = await crud.participant.from_schema_to_db_model(db_tests, obj_in=p_in)
    assert ("type_name" and "status_name" and "status_id") not in p_dict
    assert "type_id" in p_dict
    assert p_dict["type_id"] == db_p_type.id


async def test_from_schema_to_model_db_with_update_schema_status_name(db_tests: AsyncSession) -> None:
    p_status_name = ut.random_list_elem(settings.PARTICIPANT_STATUS)
    db_p_status = await crud.participant_status.get_by_name(db_tests, p_status_name)
    p_in = ParticipantUpdate(status_name=p_status_name)
    p_dict = await crud.participant.from_schema_to_db_model(db_tests, obj_in=p_in)
    assert ("type_name" and "status_name" and "type_id") not in p_dict
    assert "status_id" in p_dict
    assert p_dict["status_id"] == db_p_status.id


async def test_from_schema_to_model_db_with_update_schema(db_tests: AsyncSession) -> None:
    p_type_name = ut.random_list_elem(list(settings.PARTICIPANT_TYPES_NB_SESSION_WEEK.keys()))
    p_status_name = ut.random_list_elem(settings.PARTICIPANT_STATUS)
    db_p_type = await crud.participant_type.get_by_name(db_tests, p_type_name)
    db_p_status = await crud.participant_status.get_by_name(db_tests, p_status_name)
    p_in = ParticipantUpdate(type_name=p_type_name, status_name=p_status_name)
    p_dict = await crud.participant.from_schema_to_db_model(db_tests, obj_in=p_in)
    assert ("type_name" and "status_name") not in p_dict
    assert ("type_id" and "status_id") in p_dict
    assert p_dict["type_id"] == db_p_type.id
    assert p_dict["status_id"] == db_p_status.id


async def test_get_nb_session_week(db_tests: AsyncSession) -> None:
    participant = await ut.create_random_participant(db_tests)
    nb_session_week = (await crud.participant_type.get(db_tests, id=participant.type_id)).nb_session_week
    p_nb_session_week = await crud.participant.get_nb_session_week(db_tests, participant.id)
    assert nb_session_week == p_nb_session_week
