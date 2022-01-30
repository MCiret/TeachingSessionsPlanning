from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.crud.base import CRUDBase
from app.models import SessionStatus
from app.schemas import SessionStatusCreate, SessionStatusUpdate


class CRUDSessionStatus(CRUDBase[SessionStatus, SessionStatusCreate, SessionStatusUpdate]):
    async def get_by_name(self, db: AsyncSession, name: str) -> SessionStatus | None:
        db_obj = await db.execute(select(self.model).where(self.model.name == name))
        return db_obj.scalar()


session_status = CRUDSessionStatus(SessionStatus)
