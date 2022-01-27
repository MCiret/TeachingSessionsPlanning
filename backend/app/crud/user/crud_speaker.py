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

    async def get_day_free_time(self, db: AsyncSession, *, db_obj: Speaker, date: dt.date) -> dict[str, dt.datetime]:
        day_sessions_spk = [session for session in await crud.session.get_by_speaker_email(db, email=db_obj.email)
                            if session.date == date]
        # build a list with all speaker's sessions start times
        # adding also "start time" of the Xth session for a participant having nb_session_week = X.
        # ==> 1 speaker's session with a 2 session_week participant <=> 2 consecutive start times added in the list
        day_sessions_start_times = []
        for session in day_sessions_spk:
            day_sessions_start_times.append(session.time)
            nb_session_participant = await crud.participant.get_nb_session_week(db, id=session.participant_id)
            if nb_session_participant > 1:
                for i in range(nb_session_participant):
                    day_sessions_start_times.append((dt.datetime.combine(session.date, session.time)
                                                     + dt.timedelta(minutes=db_obj.slot_time * nb_session_participant))
                                                    .time())

        real_day_availabilities = []
        for availability in await crud.availability\
                                      .get_by_day_and_speaker_email(db, speaker_email=db_obj.email, day=date):
            if availability.time not in day_sessions_start_times:
                real_day_availabilities.append(availability.time)

        return real_day_availabilities


speaker = CRUDSpeaker(Speaker)
