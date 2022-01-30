from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.crud.base import CRUDBase
from app.models import SessionType
from app.schemas import SessionTypeCreate, SessionTypeUpdate


class CRUDSessionType(CRUDBase[SessionType, SessionTypeCreate, SessionTypeUpdate]):
    async def get_by_name(self, db: AsyncSession, name: str) -> SessionType | None:
        db_obj = await db.execute(select(self.model).where(self.model.name == name))
        return db_obj.scalar()


session_type = CRUDSessionType(SessionType)
