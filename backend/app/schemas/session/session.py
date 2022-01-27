import datetime as dt

from pydantic import BaseModel, Field

from app.core.config import settings


class SessionBase(BaseModel):
    date: dt.date
    time: dt.time
    comments: str = None
    participant_id: int = Field(None, example=("⚠️ Remove this field if you are a participant and creating a session "
                                               "for you. But if you are a speaker, you have to set this field with "
                                               "an existing participant id"))
    type_name: str
    status_name: str

    class Config:
        schema_extra = {
            "example": {
                "date": "yyyy-mm-dd",
                "time": "hr:min:sec",
                "comments": "Comments about the session...",
                "participant_id": "integer",
                "type_name": f"Choose in this list : {settings.SESSION_TYPES}",
                "status_name": f"Choose in this list : {settings.SESSION_STATUS}"
            }
        }


class SessionCreate(SessionBase):
    pass


class SessionUpdate(SessionBase):
    date: dt.date = None
    time: dt.time = None
    comments: str = None
    participant_id: int = None
    type_name: str = None
    status_name: str = None


class SessionInDBBase(BaseModel):
    id: int
    date: dt.date
    time: dt.time
    comments: str = None
    participant_id: int
    type_id: int
    status_id: int

    class Config:
        orm_mode = True


class Session(SessionInDBBase):
    type_name: str
    status_name: str


class SessionInDB(SessionInDBBase):
    pass
