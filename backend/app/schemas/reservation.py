from pydantic import BaseModel


class ReservationBase(BaseModel):
    participant_id: int
    reservation_id: int


class ReservationCreate(ReservationBase):
    pass


class ReservationUpdate(ReservationBase):
    pass


class ReservationInDBBase(ReservationBase):

    class Config:
        orm_mode = True


class Reservation(ReservationInDBBase):
    pass


class ReservationInDB(ReservationInDBBase):
    pass
