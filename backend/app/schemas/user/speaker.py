from app.schemas.user.user import UserBase, UserCreate, UserUpdate, UserInDBBase, UserInDB, User


class SpeakerBase(UserBase):
    slot_time: int


class SpeakerCreate(SpeakerBase, UserCreate):
    pass


class SpeakerUpdate(UserUpdate):
    slot_time: int = None


class SpeakerInDBBase(SpeakerBase, UserInDBBase):
    pass


class Speaker(SpeakerInDBBase, User):
    pass


class SpeakerInDB(SpeakerInDBBase, UserInDB):
    pass
