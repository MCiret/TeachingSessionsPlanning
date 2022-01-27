from typing import Optional

from pydantic import BaseModel


class ParticipantTypeBase(BaseModel):
    name: str
    nb_session_week: int


class ParticipantTypeCreate(ParticipantTypeBase):
    pass


class ParticipantTypeUpdate(ParticipantTypeBase):
    name: Optional[str] = None
    nb_session_week: Optional[int] = None


class ParticipantTypeInDBBase(ParticipantTypeBase):
    id: int

    class Config:
        orm_mode = True


class ParticipantType(ParticipantTypeInDBBase):
    pass


class ParticipantTypeInDB(ParticipantTypeInDBBase):
    pass
