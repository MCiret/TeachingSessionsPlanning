from typing import Optional

from pydantic import BaseModel


class ParticipantStatusBase(BaseModel):
    name: str


class ParticipantStatusCreate(ParticipantStatusBase):
    pass


class ParticipantStatusUpdate(ParticipantStatusBase):
    name: Optional[str] = None


class ParticipantStatusInDBBase(ParticipantStatusBase):
    id: int

    class Config:
        orm_mode = True


class ParticipantStatus(ParticipantStatusInDBBase):
    pass


class ParticipantStatusInDB(ParticipantStatusInDBBase):
    pass
