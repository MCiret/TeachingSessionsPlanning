import datetime as dt

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import aliased

from app import crud
from app.utils import add_time
from app.crud.user.crud_user import CRUDUser
from app.models import Speaker, Participant
from app.schemas import SpeakerCreate, SpeakerUpdate, SessionCreate


class CRUDSpeaker(CRUDUser[Speaker, SpeakerCreate, SpeakerUpdate]):
    async def create(self, db: AsyncSession, *, obj_in: SpeakerCreate) -> Speaker:
        return await super().create(db, obj_in=obj_in)

    async def get_by_participant_id(self, db: AsyncSession, participant_id: int) -> Speaker:
        part = aliased(Participant, flat=True)  # https://sqlalche.me/e/14/xaj2
        return (await db.execute(select(self.model)
                                 .join(part, part.speaker_id == self.model.id)
                                 .where(part.id == participant_id))).scalar()

    async def get_sessions_times_by_date(self, db: AsyncSession, db_obj: Speaker, date: dt.date) -> list[dt.time]:
        """
        Return a list with all date speaker's sessions start times (with 2 consecutive start times for a session
        with a participant having 2 sessions week..).
        """
        spk_date_sessions = await crud.session.get_by_date_speaker(db, date, db_obj.id)
        # build a list with all date speaker's sessions start times (with 2 consecutives start times for a session
        # with a participant having 2 sessions week..)
        day_sessions_start_times = []
        for session in spk_date_sessions:
            day_sessions_start_times.append(session.time)
            part_nb_sess_week = await crud.participant.get_nb_session_week(db, session.participant_id)
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

    async def is_free_for_session(self, db: AsyncSession, db_obj: Speaker, session_in: SessionCreate) -> bool:
        """
        Checks if Speaker is free for a session te be created :
         - Does he have an availability on same weekday and time concerning this date ?
            - If yes, does he already have a session on this date at same time ?
         """
        # If speaker has not a corresponding availability, no need to check more :
        if not await crud.availability.get_one_around_date_same_weekday_time_speaker(db, db_obj.id, session_in.date,
                                                                               session_in.time):
            return False

        # Else, speaker has a corresponding availability => check if it is free (i.e no other session) :
        speaker_date_free_sessions_times = await self.get_free_sessions_times_by_date(db, db_obj, session_in.date)
        if session_in.time in speaker_date_free_sessions_times:
            session_in_participant_nb_session_week = await crud.participant\
                                                               .get_nb_session_week(db, session_in.participant_id)
            # if session start time is free and participant has 1 session week => simplest case
            if session_in_participant_nb_session_week < 2:
                return True
            # else session start time is free but participant has more than 1 session week
            # => check if the whole slot time if free :
            else:
                for i in range(1, session_in_participant_nb_session_week):
                    time_to_check = add_time(date=session_in.date, time=session_in.time,
                                             minutes_to_add=i * db_obj.slot_time)
                    if time_to_check not in speaker_date_free_sessions_times:
                        return False
                return True
        else:
            return False


speaker = CRUDSpeaker(Speaker)
