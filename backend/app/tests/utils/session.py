from datetime import date, time, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.core.config import settings
from app.schemas import SessionCreate
from app.models import Session
from app.tests import utils as ut


async def create_random_session(db: AsyncSession, date_: date = None, time_: time = None,
                                participant_id: int = None) -> Session:
    if date_ is None:
        date_ = date.today()
    if time_ is None:
        time_ = datetime.now().time()
    if participant_id is None:
        participant_id = (await ut.create_random_participant(db)).id
    s_type = ut.random_list_elem(settings.SESSION_TYPES)
    s_status = ut.random_list_elem(settings.SESSION_STATUS)
    session_in = SessionCreate(date=date_, time=time_,
                               participant_id=participant_id, type_name=s_type, status_name=s_status)
    session = await crud.session.create(db=db, obj_in=session_in)
    return session
