from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.user.crud_user import CRUDUser
from app.models import Admin
from app.schemas import AdminCreate, AdminUpdate


class CRUDAdmin(CRUDUser[Admin, AdminCreate, AdminUpdate]):
    async def create(self, db: AsyncSession, *, obj_in: AdminCreate) -> Admin:
        return await super().create(db, obj_in=obj_in)


admin = CRUDAdmin(Admin)
