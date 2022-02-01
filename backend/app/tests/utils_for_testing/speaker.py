from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models
from app.schemas import SpeakerCreate, SpeakerUpdate
import app.tests.utils_for_testing as ut


async def create_random_speaker(db: AsyncSession, *, email: str = None, api_key: str = None,
                                slot_time: int = None) -> models.Speaker:
    if email is None:
        email = ut.random_email()
    if api_key is None:
        api_key = ut.random_lower_string(32)
    if slot_time is None:
        slot_time = ut.random_five_multiple_number()
    speaker_in = SpeakerCreate(
        email=email,
        api_key=api_key, first_name=ut.random_lower_string(6),
        last_name=ut.random_lower_string(6), slot_time=slot_time)
    speaker = await crud.speaker.create(db=db, obj_in=speaker_in)
    return speaker


async def speaker_authentication_token_from_email(
    *, client: AsyncClient, email: str, db: AsyncSession
) -> dict[str, str]:
    """
    Return a valid token for the speaker with given email.
    If the speaker doesn't exist it is created first.
    """
    api_key = ut.random_lower_string(32)
    speaker = await crud.user.get_by_email(db, email=email)
    if not speaker:
        await create_random_speaker(db, email=email, api_key=api_key)
    else:
        speaker_in_update = SpeakerUpdate(api_key=api_key)
        speaker = await crud.speaker.update(db, db_obj=speaker, obj_in=speaker_in_update)

    return await ut.get_not_admin_user_authentication_headers(client=client, email=email, api_key=api_key)
