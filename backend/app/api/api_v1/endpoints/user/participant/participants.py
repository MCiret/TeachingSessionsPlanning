from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.api import deps

router = APIRouter()


@router.get("/", response_model=list[schemas.Participant])
async def read_participants(
    db: AsyncSession = Depends(deps.get_async_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_speaker_or_admin_user),
) -> Any:
    """
    Read all participant users in db.
    **Allowed for speaker or admin user only.**
    """
    db_participants = await crud.participant.get_multi(db, skip=skip, limit=limit)
    participants = []
    for db_p in db_participants:
        participants.append(await crud.participant.from_db_model_to_schema(db, db_p))
    return participants


@router.post("/participant", response_model=schemas.Participant)
async def create_participant(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    participant_in: schemas.ParticipantCreate,
    current_user: models.User = Depends(deps.get_current_active_speaker_or_admin_user),
) -> Any:
    """
    Create new participant user and send him/her an email.
    **Allowed for speaker or admin user only.**
    """
    db_participant = await crud.user.get_by_email(db, email=participant_in.email)
    if db_participant:
        raise HTTPException(status_code=400, detail="A user with this email already exists in the system...")

    participant_in.speaker_id = await crud.participant.speaker_checks_and_get_id(db, participant_in,
                                                                                 current_user=current_user)
    await crud.participant.type_and_status_names_checks(db, participant_in)

    participant = await crud.participant.create(db, obj_in=participant_in)
    return await crud.participant.from_db_model_to_schema(db, participant)


@router.put("/{participant_id}", response_model=schemas.Participant)
async def update_participant_by_id(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    participant_id: int,
    participant_in: schemas.ParticipantUpdate,
    current_user: models.User = Depends(deps.get_current_active_speaker_or_admin_user),
) -> Any:
    """
    Update a participant user using id.
    **Allowed for speaker or admin user only.**
    """
    if await crud.user.get_by_email(db, email=participant_in.email):
        raise HTTPException(
            status_code=400, detail="A user with this email already exists in the system...")

    db_participant = await crud.participant.get(db, id=participant_id)
    if not db_participant:
        raise HTTPException(
            status_code=404,
            detail="A participant user with this id does not exist in the system...",
        )

    if participant_in.speaker_id:
        participant_in.speaker_id = await crud.participant.speaker_checks_and_get_id(db, participant_in,
                                                                                     current_user=current_user)
    await crud.participant.type_and_status_names_checks(db, participant_in)

    participant = await crud.participant.update(db, db_obj=db_participant, obj_in=participant_in)
    return await crud.participant.from_db_model_to_schema(db, participant)
