from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.core.config import settings
from app.models import Participant
from app.schemas import ParticipantCreate, ParticipantUpdate
from app.tests import utils as ut


async def create_random_participant(db: AsyncSession, *, email: str = None, api_key: str = None,
                                    speaker_id: int = None, p_type_name: str = None) -> Participant:
    if speaker_id is None:
        speaker_id = (await ut.create_random_speaker(db)).id
    if email is None:
        email = ut.random_email()
    if api_key is None:
        api_key = ut.random_lower_string(32)
    if p_type_name is None:
        p_type_name = ut.random_list_elem(list(settings.PARTICIPANT_TYPES_NB_SESSION_WEEK.keys()))
    participant_in = ParticipantCreate(
        email=email, type_name=p_type_name, speaker_id=speaker_id,
        api_key=api_key, first_name=ut.random_lower_string(6),
        last_name=ut.random_lower_string(6))
    participant = await crud.participant.create(db=db, obj_in=participant_in)
    return participant


async def participant_authentication_token_from_email(
    *, client: AsyncClient, email: str, db: AsyncSession
) -> dict[str, str]:
    """
    Return a valid token for the participant with given email.
    If the participant doesn't exist it is created first.
    """
    api_key = ut.random_lower_string(32)
    participant = await crud.user.get_by_email(db, email=email)
    if not participant:
        await create_random_participant(db, email=email, api_key=api_key)
    else:
        participant_in_update = ParticipantUpdate(api_key=api_key)
        participant = await crud.participant.update(db, db_obj=participant, obj_in=participant_in_update)

    return await ut.get_not_admin_user_authentication_headers(client=client, email=email, api_key=api_key)
