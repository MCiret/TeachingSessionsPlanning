from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.crud.base import CRUDBase
from app.models import ParticipantStatus
from app.schemas import ParticipantStatusCreate, ParticipantStatusUpdate


class CRUDParticipantStatus(CRUDBase[ParticipantStatus, ParticipantStatusCreate, ParticipantStatusUpdate]):
    async def get_by_name(self, db: AsyncSession, *, name: str) -> ParticipantStatus | None:
        db_obj = await db.execute(select(self.model).where(self.model.name == name))
        return db_obj.scalar()


participant_status = CRUDParticipantStatus(ParticipantStatus)
