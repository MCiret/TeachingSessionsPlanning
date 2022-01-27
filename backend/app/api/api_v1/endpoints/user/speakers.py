from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.api import deps

router = APIRouter()


@router.get("/speakers/", response_model=list[schemas.Speaker])
async def read_speakers(
    db: AsyncSession = Depends(deps.get_async_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_admin_user),
) -> Any:
    """
    Read all speaker users in db.
    **Allowed for admin user only.**
    """
    speakers = await crud.speaker.get_multi(db, skip=skip, limit=limit)
    return speakers


@router.post("/speaker", response_model=schemas.Speaker)
async def create_speaker(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    speaker_in: schemas.SpeakerCreate,
    current_user: models.User = Depends(deps.get_current_active_admin_user),
) -> Any:
    """
    Create new speaker user and send him/her an email.
    **Allowed for admin user only.**
    """
    db_speaker = await crud.user.get_by_email(db, email=speaker_in.email)
    if db_speaker:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists in the system...",
        )
    speaker = await crud.speaker.create(db, obj_in=speaker_in)
    return speaker


@router.put("/speaker/{speaker_id}", response_model=schemas.Speaker)
async def update_speaker(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    speaker_id: int,
    speaker_in: schemas.SpeakerUpdate,
    current_user: models.User = Depends(deps.get_current_active_admin_user),
) -> Any:
    """
    Update a speaker user using id.
    **Allowed for admin user only.**
    """
    if await crud.user.get_by_email(db, email=speaker_in.email):
        raise HTTPException(
            status_code=400, detail="A user with this email already exists in the system...")
    db_speaker = await crud.speaker.get(db, id=speaker_id)
    if not db_speaker:
        raise HTTPException(
            status_code=404,
            detail="A speaker user with this id does not exist in the system...",
        )
    speaker = await crud.speaker.update(db, db_obj=db_speaker, obj_in=speaker_in)
    return speaker
