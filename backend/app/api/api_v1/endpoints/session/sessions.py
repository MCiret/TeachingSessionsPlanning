from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.api import deps

router = APIRouter()


@router.get("/", response_model=list[schemas.Session])
async def read_all_sessions(
    db: AsyncSession = Depends(deps.get_async_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_speaker_or_admin_user),
) -> Any:
    """
    Read all sessions in db.
    **Allowed for speaker or admin user only.**
    """
    db_sessions = await crud.session.get_multi(db, skip=skip, limit=limit)
    sessions = []
    for db_p in db_sessions:
        sessions.append(await crud.session.from_db_model_to_schema(db, db_p))
    return sessions


@router.get("/mine", response_model=list[schemas.Session])
async def read_sessions_mine(
    db: AsyncSession = Depends(deps.get_async_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_speaker_or_participant_user),
) -> Any:
    """
    Read your sessions.
    **Allowed for speaker or participant user only.**
    """
    if current_user.profile == "participant":
        db_sessions = await crud.session.get_by_participant_email(db, participant_email=current_user.email)
    if current_user.profile == "speaker":
        db_sessions = await crud.session.get_by_speaker_email(db, speaker_email=current_user.email)
    sessions = []
    for db_p in db_sessions:
        sessions.append(await crud.session.from_db_model_to_schema(db, db_p))
    return sessions


@router.post("", response_model=schemas.Session)
async def create_session(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    session_in: schemas.SessionCreate,
    current_user: models.User = Depends(deps.get_current_active_speaker_or_participant_user)
) -> Any:  # * enforce next params te be keyword-only
    """
    Create new session and send an email to the concerned participant.
    **Allowed for speaker or participant user only.**
    """
    # for sessions with same date and time
    for sessions in await crud.session.get_by_date_and_time(db, date=session_in.date, time=session_in.time):
        session_in_speaker_id = (await crud.participant.get(db, id=session_in.participant_id)).speaker_id
        for session in sessions:
            # if a same time and date session also have the same speaker id
            if session.participant.speaker_id == session_in_speaker_id:
                raise HTTPException(
                    status_code=400,
                    detail="A session with same date, time and speaker already exists in the system...",
                )
    session_in.participant_id = await crud.session.participant_checks_and_get_id(db, session_in, current_user)
    await crud.session.type_and_status_names_checks(db, session_in)

    session = await crud.session.create(db, obj_in=session_in)
    # if settings.EMAILS_ENABLED and user_in.email:
    #     send_new_account_email(
    #         email_to=user_in.email, username=user_in.email, api_key=user_in.password
    #     )

    return await crud.session.from_db_model_to_schema(db, session)


# @router.put("/{session_id}", response_model=schemas.Session)
# async def update_session_by_id(
#     *,
#     db: AsyncSession = Depends(deps.get_async_db),
#     session_id: int,
#     session_in: schemas.SessionUpdate,
#     current_user: models.User = Depends(deps.get_current_active_admin_user),
# ) -> Any:  # * enforce next params te be keyword-only
#     """
#     Update a session using id.
#     **Allowed for admin user only.**
#     """
#     db_session = await crud.session.get(db, id=session_id)
#     if not db_session:
#         raise HTTPException(
#             status_code=404,
#             detail="A session with this id does not exist in the system...",
#         )
#     session = await crud.session.update(db, db_obj=db_session, obj_in=session_in)
#     return session
