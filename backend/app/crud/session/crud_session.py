import datetime as dt
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.encoders import jsonable_encoder
from fastapi import HTTPException

from app.crud.base import CRUDBase
from app import crud
from app.models import Session, Participant, User
from app.schemas import SessionCreate, SessionUpdate
from app.schemas import Session as SessionSchema
from app.utils import add_time


class CRUDSession(CRUDBase[Session, SessionCreate, SessionUpdate]):
    # async def get_speaker(self,  db: AsyncSession, db_obj: Session) -> list[Speaker]:
    #     spk = aliased(Speaker, flat=True)
    #     return (await db.execute(select(spk)
    #                             .join(Participant, spk.id == Participant.speaker_id)
    #                             .join(self.model, Participant.id == self.model.participant_id)
    #                             .where(self.model.participant_id == db_obj.participant_id))).scalar()

    async def get_by_participant_email(self, db: AsyncSession, *, participant_email: str) -> list[Session]:
        participant_id = (await crud.user.get_by_email(db, email=participant_email)).id
        return (await db.execute(select(self.model)
                                 .where(self.model.participant_id == participant_id))).scalars().all()

    async def get_by_speaker_email(self, db: AsyncSession, *, speaker_email: str) -> list[Session]:
        speaker_id = (await crud.user.get_by_email(db, email=speaker_email)).id
        return (await db.execute(select(self.model)
                                 .join(Participant, self.model.participant_id == Participant.id)
                                 .where(Participant.speaker_id == speaker_id))).scalars().all()

    async def get_by_date_and_time(self, db: AsyncSession, *, date: dt.date, time: dt.time) -> list[Session] | None:
        return (await db.execute(select(self.model)
                                 .where(self.model.date == date, self.model.time == time))).scalars().all()

    async def is_whole_slot_time_free(self,  db: AsyncSession, *, obj_in: SessionCreate | SessionUpdate) -> bool:
        """Checks if speaker is really free for the session to be created..."""

        obj_in_speaker = await crud.speaker.get_by_participant_id(db, participant_id=obj_in.participant_id)

        # If speaker has not a corresponding availability, no need to check more :
        if not crud.availability.get_by_date_time_speaker(db, speaker_id=obj_in_speaker.id,
                                                          date=obj_in.date, time=obj_in.time):
            return False
        # Else, speaker has a corresponding availability => check if it is free (i.e no other session) :
        speaker_day_free_times = await crud.speaker.get_day_free_time(db, bd_obj=obj_in_speaker, data=obj_in.date)
        if obj_in.time in speaker_day_free_times:
            obj_in_participant_nb_session_week = await crud.participant\
                                                           .get_nb_session_week(db, id=obj_in.participant_id)
            # session start time is free and participant has 1 session week => simplest case
            if obj_in_participant_nb_session_week < 2:
                return True
            # session start time is free but participant has more than 1 session week
            # => check if the whole slot time if free :
            else:
                for i in range(1, obj_in_participant_nb_session_week):
                    time_to_check = add_time(date=obj_in.date, time=obj_in.time,
                                             minutes_to_add=i * obj_in_speaker.slot_time)
                    if time_to_check not in speaker_day_free_times:
                        return False
                return True
        else:
            return False

    async def create(self, db: AsyncSession, *, obj_in: SessionCreate) -> Session:
        return await super().create(db, obj_in=await self.from_schema_to_db_model(db, obj_in=obj_in))

    async def update(self, db: AsyncSession, *, db_obj: Session, obj_in: SessionUpdate | dict[str, Any]) -> Session:
        return await super().update(db, db_obj=db_obj, obj_in=await self.from_schema_to_db_model(db, obj_in=obj_in))

    async def before_create_or_update_participant_checks_and_get_id(self, db: AsyncSession,
                                                                    obj_in: SessionCreate | SessionUpdate,
                                                                    current_user: User) -> int | None:
        """
        To set the session.participant_id to the current user's id if it is participant user.
        Else, if it is a speaker user, to check if the participant_id (for session creating/updating) is set if
        and if this participant_id exists in db.
        """
        if await crud.user.is_participant(current_user):
            return current_user.id
        elif obj_in.participant_id is None:
            raise HTTPException(
                status_code=400,
                detail="If you are not a Participant user, you have to set the participant_id value...")
        elif not await crud.participant.get(db, id=obj_in.participant_id):
            raise HTTPException(
                status_code=400, detail="A participant user with this id does not exist in the system...")
        else:
            return obj_in.participant_id

    async def before_create_or_update_type_and_status_names_checks(self, db: AsyncSession,
                                                                   obj_in: SessionCreate | SessionUpdate) -> None:
        """To checks if the type and status names (used for session creating/updating) exists in db."""
        if obj_in.type_name and not await crud.session_type.get_by_name(db, name=obj_in.type_name):
            raise HTTPException(
                status_code=400, detail=f"Type {obj_in.type_name} does not exists...")
        if obj_in.status_name and not await crud.session_status.get_by_name(db, name=obj_in.status_name):
            raise HTTPException(
                status_code=400, detail=f"Status {obj_in.status_name} does not exists...")

    async def from_schema_to_db_model(self, db: AsyncSession, *, obj_in: SessionCreate | SessionUpdate) -> dict:
        """ Build the SQLAlchemy model Session (with the good field) to insert in db. """
        if isinstance(obj_in, SessionCreate):
            obj_in_data = jsonable_encoder(obj_in)
        elif isinstance(obj_in, SessionUpdate):
            obj_in_data = jsonable_encoder(obj_in, exclude_unset=True)
        if obj_in_data.get("type_name"):
            obj_in_data.update([
                ("type_id", (await crud.session_type.get_by_name(db, name=obj_in.type_name)).id)
            ])
            del obj_in_data["type_name"]
        if obj_in_data.get("status_name"):
            obj_in_data.update([
                ("status_id", (await crud.session_status.get_by_name(db, name=obj_in.status_name)).id)
            ])
            del obj_in_data["status_name"]
        if obj_in_data.get("date"):
            obj_in_data.update([("date", dt.date.fromisoformat(obj_in_data["date"]))])
        if obj_in_data.get("time"):
            obj_in_data.update([("time", dt.time.fromisoformat(obj_in_data["time"]))])
        return obj_in_data

    async def from_db_model_to_schema(self, db: AsyncSession, db_obj: Session) -> SessionSchema:
        """ Build the pydantic schema Session (with the good field) to return/display to user/client. """
        s_type_name = (await crud.session_type.get(db, id=db_obj.type_id)).name
        s_status_name = (await crud.session_status.get(db, id=db_obj.status_id)).name
        return SessionSchema(**jsonable_encoder(db_obj), type_name=s_type_name, status_name=s_status_name)


session = CRUDSession(Session)
