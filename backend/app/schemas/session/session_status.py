from typing import Optional

from pydantic import BaseModel


class SessionStatusBase(BaseModel):
    name: str


class SessionStatusCreate(SessionStatusBase):
    pass


class SessionStatusUpdate(SessionStatusBase):
    name: Optional[str] = None


class SessionStatusInDBBase(SessionStatusBase):
    id: int

    class Config:
        orm_mode = True


class SessionStatus(SessionStatusInDBBase):
    pass


class SessionStatusInDB(SessionStatusInDBBase):
    pass
