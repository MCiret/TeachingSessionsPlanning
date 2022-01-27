import datetime as dt

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import aliased

from app import crud
from app.crud.user.crud_user import CRUDUser
from app.models import Speaker, Participant
from app.schemas import SpeakerCreate, SpeakerUpdate


class CRUDSpeaker(CRUDUser[Speaker, SpeakerCreate, SpeakerUpdate]):
    async def create(self, db: AsyncSession, *, obj_in: SpeakerCreate) -> Speaker:
        return await super().create(db, obj_in=obj_in)

    async def get_by_participant_id(self, db: AsyncSession, *, participant_id: int) -> Speaker:
        part = aliased(Participant, flat=True)  # https://sqlalche.me/e/14/xaj2
        return (await db.execute(select(self.model)
                                 .join(part, part.speaker_id == self.model.id)
                                 .where(part.id == participant_id))).scalar()

    async def get_sessions_times_by_date(self, db: AsyncSession, db_obj: Speaker, date: dt.date) -> list[dt.time]:
        """
        Return a list with all date speaker's sessions start times (with 2 consecutive start times for a session
        with a participant having 2 sessions week..).
        """
        spk_date_sessions = await crud.session.get_by_date_speaker(db, speaker_id=db_obj.id, date=date)
        # build a list with all date speaker's sessions start times (with 2 consecutives start times for a session
        # with a participant having 2 sessions week..)
        day_sessions_start_times = []
        for session in spk_date_sessions:
            day_sessions_start_times.append(session.time)
            part_nb_sess_week = await crud.participant.get_nb_session_week(db, id=session.participant_id)
            if part_nb_sess_week > 1:
                for i in range(1, part_nb_sess_week):
                    day_sessions_start_times.append((dt.datetime.combine(session.date, session.time)
                                                     + dt.timedelta(minutes=db_obj.slot_time * i))
                                                    .time())
        return day_sessions_start_times

    async def get_free_sessions_times_by_date(self, db: AsyncSession, db_obj: Speaker, date: dt.date) -> list[dt.time]:
        spk_date_sessions_times_list = await self.get_sessions_times_by_date(db, db_obj, date)
        spk_date_avails_times_list = await crud.availability.get_times_list_by_date_speaker(db, db_obj.id, date)

        spk_date_free_sessions_times = []
        for av_time in spk_date_avails_times_list:
            if av_time not in spk_date_sessions_times_list:
                spk_date_free_sessions_times.append(av_time)

        return spk_date_free_sessions_times


speaker = CRUDSpeaker(Speaker)
