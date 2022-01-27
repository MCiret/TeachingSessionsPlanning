from typing import Optional

from pydantic import BaseModel


class SessionTypeBase(BaseModel):
    name: str


class SessionTypeCreate(SessionTypeBase):
    pass


class SessionTypeUpdate(SessionTypeBase):
    name: Optional[str] = None


class SessionTypeInDBBase(SessionTypeBase):
    id: int

    class Config:
        orm_mode = True


class SessionType(SessionTypeInDBBase):
    pass


class SessionTypeInDB(SessionTypeInDBBase):
    pass
