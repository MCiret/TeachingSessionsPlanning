from app.schemas.user.user import UserBase, UserCreate, UserUpdate, UserInDBBase, User, UserInDB


class AdminBase(UserBase):
    pass


class AdminCreate(AdminBase, UserCreate):
    pass


class AdminUpdate(UserUpdate):
    pass


class AdminInDBBase(AdminBase, UserInDBBase):
    pass


class Admin(AdminInDBBase, User):
    pass


class AdminInDB(AdminInDBBase, UserInDB):
    pass
