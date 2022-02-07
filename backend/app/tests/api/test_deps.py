import pytest
from fastapi import HTTPException
import jose

from app.api import deps

# This is the same as using the @pytest.mark.anyio on all test functions in the module
pytestmark = pytest.mark.anyio


async def test_get_current_user_jwt_ok_and_user_found(mocker):
    mock_decode = mocker.patch('jose.jwt.decode')
    mock_decode.return_value = {
        "access_token": "access_tok",
        "token_type": "bearer",
        "sub": 1
        }
    mock_crud_user_get = mocker.patch('app.crud.user.get')
    mock_crud_user_get.return_value = "user found and authenticate!"
    assert await deps.check_jwt_and_get_current_user() == "user found and authenticate!"
    mock_decode.assert_called_once()
    mock_crud_user_get.assert_called_once()


async def test_get_current_user_jwt_validation_error_raises_HTTPException(mocker):
    mock_decode = mocker.patch('jose.jwt.decode')
    mock_decode.return_value = {
        "access_token": "access_tok",
        "token_type": "bearer",
        "sub": "str user id"  # to produce the pydantic ValidationError
        }
    mock_crud_user_get = mocker.patch('app.crud.user.get')
    with pytest.raises(HTTPException) as he:
        await deps.check_jwt_and_get_current_user()
    assert "Could not validate credentials" in str(he.getrepr())
    mock_decode.assert_called_once()
    mock_crud_user_get.assert_not_called()


async def test_get_current_user_jwt_JWTError_raises_HTTPException(mocker):
    mock_decode = mocker.patch('jose.jwt.decode')
    mock_decode.side_effect = jose.jwt.JWTError
    mock_crud_user_get = mocker.patch('app.crud.user.get')
    with pytest.raises(HTTPException) as he:
        await deps.check_jwt_and_get_current_user()
    assert "Could not validate credentials" in str(he.getrepr())
    mock_decode.assert_called_once()
    mock_crud_user_get.assert_not_called()


async def test_get_current_user_jwt_ok_but_user_not_found_raises_HTTPException(mocker):
    mock_decode = mocker.patch('jose.jwt.decode')
    mock_decode.return_value = {
        "access_token": "access_tok",
        "token_type": "bearer",
        "sub": 1
        }
    mock_crud_user_get = mocker.patch('app.crud.user.get')
    mock_crud_user_get.return_value = False
    with pytest.raises(HTTPException) as he:
        await deps.check_jwt_and_get_current_user()
    assert "User not found" in str(he.getrepr())
    mock_decode.assert_called_once()
    mock_crud_user_get.assert_called_once()


async def test_get_current_active_user_active_user(mocker):
    mock_crud_user_is_active = mocker.patch('app.crud.user.is_active')
    mock_crud_user_is_active.return_value = True
    assert await deps.get_current_active_user()
    mock_crud_user_is_active.assert_called_once()


async def test_get_current_active_user_inactive_user_raises_HTTPException(mocker):
    mock_crud_user_is_active = mocker.patch('app.crud.user.is_active')
    mock_crud_user_is_active.return_value = False
    with pytest.raises(HTTPException) as he:
        await deps.get_current_active_user()
    assert "Inactive user" in str(he.getrepr())
    mock_crud_user_is_active.assert_called_once()


async def test_get_current_active_speaker_or_admin_user_admin_user(mocker):
    mock_crud_user_is_speaker = mocker.patch('app.crud.user.is_speaker')
    mock_crud_user_is_speaker.return_value = False
    mock_crud_user_is_admin = mocker.patch('app.crud.user.is_admin')
    mock_crud_user_is_admin.return_value = True
    assert await deps.get_current_active_speaker_or_admin_user()
    mock_crud_user_is_speaker.assert_called_once()
    mock_crud_user_is_admin.assert_called_once()


async def test_get_current_active_speaker_or_admin_user_speaker_user(mocker):
    mock_crud_user_is_speaker = mocker.patch('app.crud.user.is_speaker')
    mock_crud_user_is_speaker.return_value = True
    mock_crud_user_is_admin = mocker.patch('app.crud.user.is_admin')
    mock_crud_user_is_admin.return_value = False
    assert await deps.get_current_active_speaker_or_admin_user()
    mock_crud_user_is_speaker.assert_called_once()
    mock_crud_user_is_admin.assert_not_called()


async def test_get_current_active_speaker_or_admin_user_both_false_raises_HTTPException(mocker):
    mock_crud_user_is_speaker = mocker.patch('app.crud.user.is_speaker')
    mock_crud_user_is_speaker.return_value = False
    mock_crud_user_is_admin = mocker.patch('app.crud.user.is_admin')
    mock_crud_user_is_admin.return_value = False
    with pytest.raises(HTTPException) as he:
        await deps.get_current_active_speaker_or_admin_user()
    assert "To do this, the user has to be a Speaker or Admin user" in str(he.getrepr())
    mock_crud_user_is_speaker.assert_called_once()
    mock_crud_user_is_admin.assert_called_once()


async def test_get_current_active_speaker_or_participant_user_speaker_user(mocker):
    mock_crud_user_is_speaker = mocker.patch('app.crud.user.is_speaker')
    mock_crud_user_is_speaker.return_value = True
    mock_crud_user_is_participant = mocker.patch('app.crud.user.is_participant')
    mock_crud_user_is_participant.return_value = False
    assert await deps.get_current_active_speaker_or_participant_user()
    mock_crud_user_is_speaker.assert_called_once()
    mock_crud_user_is_participant.assert_not_called()


async def test_get_current_active_speaker_or_participant_user_participant_user(mocker):
    mock_crud_user_is_speaker = mocker.patch('app.crud.user.is_speaker')
    mock_crud_user_is_speaker.return_value = False
    mock_crud_user_is_participant = mocker.patch('app.crud.user.is_participant')
    mock_crud_user_is_participant.return_value = True
    assert await deps.get_current_active_speaker_or_participant_user()
    mock_crud_user_is_speaker.assert_called_once()
    mock_crud_user_is_participant.assert_called_once()


async def test_get_current_active_speaker_or_participant_user_both_false_raises_HTTPException(mocker):
    mock_crud_user_is_speaker = mocker.patch('app.crud.user.is_speaker')
    mock_crud_user_is_speaker.return_value = False
    mock_crud_user_is_participant = mocker.patch('app.crud.user.is_participant')
    mock_crud_user_is_participant.return_value = False
    with pytest.raises(HTTPException) as he:
        await deps.get_current_active_speaker_or_participant_user()
    assert "To do this, the user has to be a Speaker or Participant user" in str(he.getrepr())
    mock_crud_user_is_speaker.assert_called_once()
    mock_crud_user_is_participant.assert_called_once()


async def test_get_current_active_admin_user_admin_user(mocker):
    mock_crud_user_is_admin = mocker.patch('app.crud.user.is_admin')
    mock_crud_user_is_admin.return_value = True
    assert await deps.get_current_active_admin_user()
    mock_crud_user_is_admin.assert_called_once()


async def test_get_current_active_admin_user_not_admin_user(mocker):
    mock_crud_user_is_admin = mocker.patch('app.crud.user.is_admin')
    mock_crud_user_is_admin.return_value = False
    with pytest.raises(HTTPException) as he:
        await deps.get_current_active_admin_user()
    assert "The user doesn't have enough privileges" in str(he.getrepr())
    mock_crud_user_is_admin.assert_called_once()


async def test_get_current_active_speaker_user_speaker_user(mocker):
    mock_crud_user_is_speaker = mocker.patch('app.crud.user.is_speaker')
    mock_crud_user_is_speaker.return_value = True
    assert await deps.get_current_active_speaker_user()
    mock_crud_user_is_speaker.assert_called_once()


async def test_get_current_active_speaker_user_not_speaker_user(mocker):
    mock_crud_user_is_speaker = mocker.patch('app.crud.user.is_speaker')
    mock_crud_user_is_speaker.return_value = False
    with pytest.raises(HTTPException) as he:
        await deps.get_current_active_speaker_user()
    assert "To do this, the user has to be a Speaker user" in str(he.getrepr())
    mock_crud_user_is_speaker.assert_called_once()
