import datetime as dt

from pydantic import BaseModel


class AvailabilityBase(BaseModel):
    start_date: dt.date
    end_date: dt.date
    week_day: int
    time: dt.time

    class Config:
        schema_extra = {
            "example": {
                "start_date": "yyyy-mm-dd",
                "end_date": "yyyy-mm-dd",
                "week_day": "0 = monday ... 6 = sunday",
                "time": "hr:min:sec"
            }
        }


class AvailabilityCreate(AvailabilityBase):
    pass


class AvailabilityUpdate(AvailabilityBase):
    start_date: dt.date = None
    end_date: dt.date = None
    week_day: int = None
    time: dt.time = None


class AvailabilityInDBBase(AvailabilityBase):
    id: int
    speaker_id: int

    class Config:
        orm_mode = True


class Availability(AvailabilityInDBBase):
    pass


class AvailabilityInDB(AvailabilityInDBBase):
    pass
