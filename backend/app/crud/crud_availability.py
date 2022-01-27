import datetime as dt
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.encoders import jsonable_encoder


from app.crud.base import CRUDBase
from app import crud
from app.utils import subtract_time, add_time
from app.models import Availability
from app.schemas import AvailabilityCreate, AvailabilityUpdate


class CRUDAvailability(CRUDBase[Availability, AvailabilityCreate, AvailabilityUpdate]):
    async def create(self, db: AsyncSession, *, obj_in: AvailabilityCreate, speaker_id: int) -> Availability:
        if isinstance(obj_in, dict):
            obj_in_data = obj_in
        else:
            obj_in_data = jsonable_encoder(obj_in)
        obj_in_data.update([
            ("start_date", dt.date.fromisoformat(obj_in_data["start_date"])),
            ("end_date", dt.date.fromisoformat(obj_in_data["end_date"])),
            ("time", dt.time.fromisoformat(obj_in_data["time"])),
            ("speaker_id", speaker_id)
        ])
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, *, db_obj: Availability,
                     obj_in: AvailabilityUpdate | dict[str, Any]) -> Availability:

        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def is_start_before_end_date(self, start_date: dt.date, end_date: dt.date) -> bool:
        return start_date <= end_date

    async def is_a_good_weekday_int(self, start_date: dt.date, end_date: dt.date, weekday_int: int) -> bool:
        if (end_date - start_date) < dt.timedelta(days=6):
            date_to_check = start_date
            while date_to_check <= end_date:
                if date_to_check.weekday() == weekday_int:
                    return True
                elif date_to_check == end_date:
                    return False
                else:
                    date_to_check += dt.timedelta(days=1)
        return True

    async def get_by_speaker(self, db: AsyncSession, *, speaker_id: int) -> list[Availability]:
        return (await db.execute(select(self.model)
                                 .where(self.model.speaker_id == speaker_id))).scalars().all()

    async def get_by_date_speaker(self, db: AsyncSession, *, speaker_id: int, date: dt.date) -> list[Availability]:
        week_day_int = date.weekday()  # 0 for monday ... 6 for sunday
        return (await db.execute(select(self.model)
                                 .where(self.model.speaker_id == speaker_id,
                                        self.model.week_day == week_day_int,
                                        self.model.start_date <= date,
                                        self.model.end_date >= date))).scalars().all()

    async def get_by_date_time_speaker(self, db: AsyncSession, *, speaker_id: int, date: dt.date,
                                       time: dt.time) -> Availability | None:
        week_day_int = date.weekday()  # 0 for monday ... 6 for sunday
        return (await db.execute(select(self.model)
                                 .where(self.model.speaker_id == speaker_id,
                                        self.model.week_day == week_day_int,
                                        self.model.start_date <= date,
                                        self.model.end_date >= date,
                                        self.model.time == time))).scalar_one_or_none()

    async def get_by_weekday_time_speaker(self, db: AsyncSession, *, speaker_id: int, week_day: int,
                                          time: dt.time) -> list[Availability]:
        return (await db.execute(select(self.model)
                                 .where(self.model.speaker_id == speaker_id,
                                        self.model.week_day == week_day,
                                        self.model.time == time))).scalars().all()

    async def get_by_weekday_speaker(self, db: AsyncSession, *, speaker_id: int, week_day: int) -> list[Availability]:
        return (await db.execute(select(self.model)
                                 .where(self.model.speaker_id == speaker_id,
                                        self.model.week_day == week_day))).scalars().all()

    async def is_same_period_weekday_time_exists(self, db: AsyncSession, *, speaker_id: int,
                                                 obj_in: AvailabilityCreate) -> bool:
        """
        Returns False is none this speaker's availability exists on same weekday+time
        between start and end date of obj_in.
        Returns True if at least 1 availability exists on same weekday+time between start and end date of obj_in.
        """
        db_avails = await self.get_by_weekday_time_speaker(db, speaker_id=speaker_id,
                                                           week_day=obj_in.week_day,
                                                           time=obj_in.time)
        for av in db_avails:
            if obj_in.start_date <= av.end_date:
                if obj_in.start_date >= av.start_date:
                    return True
                else:
                    if obj_in.end_date >= av.start_date:
                        return True
        return False

    async def is_same_period_weekday_exists(self, db: AsyncSession, *, speaker_id: int,
                                            obj_in: AvailabilityCreate) -> bool:
        """
        Returns False is none this speaker's availability exists on same weekday between start and end date of obj_in.
        Returns True if at least 1 availability exists on same weekday between start and end date of obj_in.
        """
        db_avails = await self.get_by_weekday_speaker(db, speaker_id=speaker_id, week_day=obj_in.week_day)
        for av in db_avails:
            if obj_in.start_date <= av.end_date:
                if obj_in.start_date >= av.start_date:
                    return True
                else:
                    if obj_in.end_date >= av.start_date:
                        return True
        return False

    async def has_too_close_previous(self, db: AsyncSession, speaker_id: int,
                                     obj_in: AvailabilityCreate) -> Availability | None:
        """
        Checks if the most close previous availability is at least 1 speaker's slot_time before the one to create.
        """
        speaker = await crud.speaker.get(db, id=speaker_id)
        if await self.is_same_period_weekday_exists(db, speaker_id=speaker.id, obj_in=obj_in):
            avails = await self.get_by_weekday_speaker(db, speaker_id=speaker_id, week_day=obj_in.week_day)
            # Calculate the time of the closest possible previous availability that would allow to create this obj_in
            # # No matter the date to calculate the time
            closest_possible_prev_time = subtract_time(date=dt.date.today(), time=obj_in.time,
                                                       minutes_to_subtract=speaker.slot_time)
            for av in avails:
                if av.time > closest_possible_prev_time and av.time < obj_in.time:
                    return True
        return False

    async def has_too_close_next(self, db: AsyncSession, speaker_id: int,
                                 obj_in: AvailabilityCreate) -> Availability | None:
        """
        Checks if the most close next availability is at least 1 speaker's slot_time after the one to create.
        """
        speaker = await crud.speaker.get(db, id=speaker_id)
        if await self.is_same_period_weekday_exists(db, speaker_id=speaker.id, obj_in=obj_in):
            avails = await self.get_by_weekday_speaker(db, speaker_id=speaker_id, week_day=obj_in.week_day)
            # Calculate the time of the closest possible next availability that would allow to create this obj_in
            # No matter the date to calculate the time
            closest_possible_next_time = add_time(date=dt.date.today(), time=obj_in.time,
                                                  minutes_to_add=speaker.slot_time)
            for av in avails:
                if av.time < closest_possible_next_time and av.time > obj_in.time:
                    return True
        return False


availability = CRUDAvailability(Availability)
