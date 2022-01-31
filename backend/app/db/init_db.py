from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas
from app.core.config import settings
# make sure all SQL Alchemy models are imported (app.db.base) before initializing DB
# otherwise, SQL Alchemy might fail to initialize relationships properly
# see https://github.com/tiangolo/full-stack-fastapi-postgresql/issues/28
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
    for pt_name in settings.PARTICIPANT_TYPES_NB_SESSION_WEEK:
        p_type = await crud.participant_type.get_by_name(db, pt_name)
        if not p_type:
            p_type = schemas.ParticipantTypeCreate(name=pt_name,
                                                   nb_session_week=settings.PARTICIPANT_TYPES_NB_SESSION_WEEK[pt_name])
            await crud.participant_type.create(db, obj_in=p_type)
    for ps_name in settings.PARTICIPANT_STATUS:
        p_status = await crud.participant_status.get_by_name(db, ps_name)
        if not p_status:
            p_status = schemas.ParticipantStatusCreate(name=ps_name)
            await crud.participant_status.create(db, obj_in=p_status)

    # Create status and types (needed for session creation) :
    for st_name in settings.SESSION_TYPES:
        s_type = await crud.session_type.get_by_name(db, st_name)
        if not s_type:
            s_type = schemas.SessionTypeCreate(name=st_name)
            await crud.session_type.create(db, obj_in=s_type)

    for ss_name in settings.SESSION_STATUS:
        s_status = await crud.session_status.get_by_name(db, ss_name)
        if not s_status:
            s_status = schemas.SessionStatusCreate(name=ss_name)
            await crud.session_status.create(db, obj_in=s_status)
