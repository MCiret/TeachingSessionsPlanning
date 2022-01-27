from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas
from app.core.config import settings
from app.db import base  # noqa


async def initialize_db(db: AsyncSession) -> None:
    """
    Create an admin user (using core/config.py data) if none exists in db.
    To run (using init_db_data.py) before launching the main app.
    """
    # To have at least one admin user :
    user = await crud.user.get_by_email(db, email=settings.FIRST_SUPERUSER_EMAIL)
    if not user:
        user_in = schemas.AdminCreate(
            first_name=settings.FIRST_SUPERUSER_FIRST_NAME,
            last_name=settings.FIRST_SUPERUSER_LAST_NAME,
            email=settings.FIRST_SUPERUSER_EMAIL,
            api_key=settings.FIRST_SUPERUSER_PASSWORD,
        )
        await crud.admin.create(db, obj_in=user_in)  # noqa: F841

    # Create status and types (needed for participant creation) :
    for pt in settings.PARTICIPANT_TYPES_NB_SESSION_WEEK:
        p_type = await crud.participant_type.get_by_name(db, name=pt)
        if not p_type:
            p_type = schemas.ParticipantTypeCreate(name=pt,
                                                   nb_session_week=settings.PARTICIPANT_TYPES_NB_SESSION_WEEK[pt])
            await crud.participant_type.create(db, obj_in=p_type)
    for ps in settings.PARTICIPANT_STATUS:
        p_status = await crud.participant_status.get_by_name(db, name=ps)
        if not p_status:
            p_status = schemas.ParticipantStatusCreate(name=ps)
            await crud.participant_status.create(db, obj_in=p_status)

    # Create status and types (needed for session creation) :
    for st in settings.SESSION_TYPES:
        s_type = await crud.session_type.get_by_name(db, name=st)
        if not s_type:
            s_type = schemas.SessionTypeCreate(name=st)
            await crud.session_type.create(db, obj_in=s_type)

    for ss in settings.SESSION_STATUS:
        s_status = await crud.session_status.get_by_name(db, name=ss)
        if not s_status:
            s_status = schemas.SessionStatusCreate(name=ss)
            await crud.session_status.create(db, obj_in=s_status)
