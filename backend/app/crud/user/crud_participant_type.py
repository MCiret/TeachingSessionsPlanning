from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.crud.base import CRUDBase
from app.models import ParticipantType
from app.schemas import ParticipantTypeCreate, ParticipantTypeUpdate


class CRUDParticipantType(CRUDBase[ParticipantType, ParticipantTypeCreate, ParticipantTypeUpdate]):
    async def get_by_name(self, db: AsyncSession, *, name: str) -> ParticipantType | None:
        db_obj = await db.execute(select(self.model).where(self.model.name == name))
        return db_obj.scalar()

    async def get_max_nb_session_week(self, db: AsyncSession) -> int:
        return max((await db.execute(select(ParticipantType.nb_session_week))).scalars().all())


participant_type = CRUDParticipantType(ParticipantType)
