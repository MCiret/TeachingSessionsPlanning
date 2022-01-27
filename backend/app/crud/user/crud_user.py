from typing import Any, TypeVar, Generic

from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models import User as model_user
from app.schemas import User as schema_user
UserType = TypeVar("UserType", bound=model_user)
CreateSchemaUserType = TypeVar("CreateSchemaUserType", bound=schema_user)
UpdateSchemaUserType = TypeVar("UpdateSchemaUserType", bound=schema_user)


class CRUDUser(CRUDBase, Generic[UserType, CreateSchemaUserType, UpdateSchemaUserType]):
    async def get_by_email(self, db: AsyncSession, *, email: str) -> UserType | None:
        db_obj = await db.execute(select(self.model).where(self.model.email == email))
        return db_obj.scalar()

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaUserType) -> UserType:
        """
        This method should never be direclty used. Only a base for subclasses creation methods.

        From SQLAlchemy doc :
        Newly saved/created Admin, Speaker or Participant objects will automatically populate
        the User.profile column with the correct “discriminator” value "admin", "speaker" or "participant".
        """
        if self.model == model_user:
            raise NotImplementedError
        if isinstance(obj_in, dict):
            obj_in_data = obj_in
            obj_in_data.update([("hashed_api_key", get_password_hash(obj_in["api_key"]))])
        else:
            obj_in_data = jsonable_encoder(obj_in)
            obj_in_data.update([("hashed_api_key", get_password_hash(obj_in.api_key))])
        del obj_in_data["api_key"]

        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, *, db_obj: UserType,
                     obj_in: UpdateSchemaUserType | dict[str, Any]) -> UserType:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        if update_data.get("api_key"):
            update_data["hashed_api_key"] = get_password_hash(update_data["api_key"])
            del update_data["api_key"]
        return await super().update(db, db_obj=db_obj, obj_in=update_data)

    async def authenticate(self, db: AsyncSession, *, email: str, api_key: str) -> UserType | None:
        user = await self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(api_key, user.hashed_api_key):
            return None
        return user

    async def is_active(self, user: UserType) -> bool:
        return user.is_active

    async def is_speaker(self, user: UserType) -> bool:
        return user.profile == "speaker"

    async def is_participant(self, user: UserType) -> bool:
        return user.profile == "participant"

    async def is_admin(self, user: UserType) -> bool:
        return user.profile == "admin"


user = CRUDUser(model_user)
