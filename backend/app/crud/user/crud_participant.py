from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.encoders import jsonable_encoder
from fastapi import HTTPException

from app import crud
from app.crud.user.crud_user import CRUDUser
from app.models import User, Participant, ParticipantType
from app.schemas import Participant as ParticipantSchema
from app.schemas import ParticipantCreate, ParticipantUpdate


class CRUDParticipant(CRUDUser[Participant, ParticipantCreate, ParticipantUpdate]):
    async def get_multi(self, db: AsyncSession, *, skip: int = 0, limit: int = 100) -> list[Participant]:
        return (await db.execute(select(self.model).offset(skip).limit(limit))).scalars().all()

    async def get_nb_session_week(self, db: AsyncSession, *, id) -> int:
        return (await db.execute(select(ParticipantType.nb_session_week)
                                 .join(self.model, self.model.type_id == ParticipantType.id)
                                 .where(self.model.id == id))).scalar()

    async def create(self, db: AsyncSession, *, obj_in: ParticipantCreate) -> Participant:
        return await super().create(db, obj_in=await self.from_schema_to_db_model(db, obj_in=obj_in))

    async def update(self, db: AsyncSession, *, db_obj: Participant,
                     obj_in: ParticipantUpdate | dict[str, Any]) -> Participant:
        return await super().update(db, db_obj=db_obj, obj_in=await self.from_schema_to_db_model(db, obj_in=obj_in))

    async def from_schema_to_db_model(self, db: AsyncSession, *,
                                      obj_in: ParticipantCreate | ParticipantUpdate) -> dict:
        """ Build the SQLAlchemy model Participant (with the good field) to insert in db. """
        if isinstance(obj_in, ParticipantCreate):
            obj_in_data = jsonable_encoder(obj_in)
        elif isinstance(obj_in, ParticipantUpdate):
            obj_in_data = jsonable_encoder(obj_in, exclude_unset=True)

        if obj_in_data.get("type_name"):
            obj_in_data.update([
                ("type_id", (await crud.participant_type.get_by_name(db, name=obj_in.type_name)).id)
            ])
            del obj_in_data["type_name"]
        if obj_in_data.get("status_name"):
            obj_in_data.update([
                ("status_id", (await crud.participant_status.get_by_name(db, name=obj_in.status_name)).id)
            ])
            del obj_in_data["status_name"]

        return obj_in_data

    async def speaker_checks_and_get_id(self, db: AsyncSession, obj_in: ParticipantCreate | ParticipantUpdate,
                                        current_user: User) -> int | None:
        """
        To set the participant.speaker_id to the current user's id if it is a speaker user.
        Else, if it is an admin user, to check if the speaker_id (for participant creating/updating) is set
        and if this speaker_id exists in db.
        """
        if await super().is_speaker(current_user):
            return current_user.id
        elif obj_in.speaker_id is None:
            raise HTTPException(
                status_code=400, detail="If you are not a Speaker user, you have to set the speaker_id value...")
        elif not await crud.speaker.get(db, id=obj_in.speaker_id):
            raise HTTPException(
                status_code=400, detail="A speaker user with this id does not exist in the system...")
        else:
            return obj_in.speaker_id

    async def type_and_status_names_checks(self, db: AsyncSession,
                                           obj_in: ParticipantCreate | ParticipantUpdate) -> None:
        """To checks if the type and status names (used for participant creating/updating) exists in db."""
        if obj_in.type_name and not await crud.participant_type.get_by_name(db, name=obj_in.type_name):
            raise HTTPException(
                status_code=400, detail=f"Type {obj_in.type_name} does not exists...")
        if obj_in.status_name and not await crud.participant_status.get_by_name(db, name=obj_in.status_name):
            raise HTTPException(
                status_code=400, detail=f"Status {obj_in.status_name} does not exists...")

    async def from_db_model_to_schema(self, db: AsyncSession, db_obj: Participant) -> ParticipantSchema:
        """ Build the pydantic schema Participant (with the good field) to return/display to user/client. """
        p_type_name = (await crud.participant_type.get(db, id=db_obj.type_id)).name
        p_status_name = (await crud.participant_status.get(db, id=db_obj.status_id)).name
        return ParticipantSchema(**jsonable_encoder(db_obj), type_name=p_type_name, status_name=p_status_name)


participant = CRUDParticipant(Participant)
