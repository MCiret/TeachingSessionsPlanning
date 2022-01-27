from typing import Optional

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    is_active: bool = True
    first_name: str
    last_name: str


class UserCreate(UserBase):
    """ Never directly used. Only a base for subclasses schemas. """
    api_key: str


class UserUpdate(UserBase):
    """
    For updating, properties have default values
    so the API user should only send values to update.
    """
    api_key: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserInDBBase(UserBase):
    id: int
    profile: str

    class Config:
        orm_mode = True


class User(UserInDBBase):
    pass


class UserInDB(UserInDBBase):
    hashed_api_key: str
