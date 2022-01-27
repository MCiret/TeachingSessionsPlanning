from typing import Optional

from pydantic import Field

from app.core.config import settings

from app.schemas.user.user import UserBase, UserCreate, UserUpdate, UserInDBBase, UserInDB
from app.schemas.reservation import Reservation


class ParticipantBase(UserBase):
    pass


class ParticipantCreate(UserCreate):
    type_name: str = Field(..., example=(f"Choose in this list : "
                                         f"{list(settings.PARTICIPANT_TYPES_NB_SESSION_WEEK.keys())}"))
    status_name: str = Field(settings.PARTICIPANT_STATUS_DEFAULT_VALUE,
                             example=(f"⚠️ Remove this field if the default "
                                      f"(i.e {settings.PARTICIPANT_STATUS_DEFAULT_VALUE}) is wanted, "
                                      f"else another one choose in this list : {settings.PARTICIPANT_STATUS}"))
    speaker_id: int = Field(None, example=("⚠️ Remove this field if you are a speaker and creating a participant "
                                           "for you. But if you are an admin, you have to set this field with "
                                           "an existing speaker id"))


class ParticipantUpdate(UserUpdate):
    type_name: Optional[str] = None
    status_name: Optional[str] = None
    speaker_id: Optional[int] = None


class ParticipantInDBBase(UserInDBBase):
    type_id: int
    status_id: int
    speaker_id: int
    reservation: Reservation = None


class Participant(ParticipantInDBBase):
    type_name: str
    status_name: str


class ParticipantInDB(ParticipantInDBBase, UserInDB):
    pass
