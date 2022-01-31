from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession


from app import crud, models, schemas
from app.api import deps

router = APIRouter()


@router.get("/status", response_model=list[schemas.ParticipantStatus])
async def read_participant_status(
    db: AsyncSession = Depends(deps.get_async_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_admin_user),
) -> Any:
    """
    **Allowed for admin user only.**
    """
    return await crud.participant_status.get_multi(db, skip=skip, limit=limit)


@router.post("/status", response_model=schemas.ParticipantStatus)
async def create_participant_status(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    status_in: schemas.ParticipantStatusCreate,
    current_user: models.User = Depends(deps.get_current_active_admin_user),
) -> Any:
    """
    **⚠️** Participant status are created during prerequisite 'init_db_data' module execution which uses set values
    in PARTICIPANT_STATUS list (core/config.py).<br>
    However, if a user would like to create a participant status, he has to uncomment this endpoint function
    and update PARTICIPANT_STATUS to update API doc.
    **Allowed for admin user only.**
    """
    if await crud.participant_status.get_by_name(db, status_in.name):
        raise HTTPException(
            status_code=400,
            detail="A participant status with this name already exists in the system...",
        )
    return await crud.participant_status.create(db, obj_in=status_in)


@router.put("/status/{status_id}", response_model=schemas.ParticipantStatus)
async def update_participant_status_by_id(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    status_id: int,
    status_in: schemas.ParticipantStatusUpdate,
    current_user: models.User = Depends(deps.get_current_active_admin_user),
) -> Any:
    """
    **⚠️** Participant status are created during prerequisite 'init_db_data' module execution which uses set values
    in PARTICIPANT_STATUS list (core/config.py).<br>
    However, if a user would like to update a participant status, he has to uncomment this endpoint function
    and update PARTICIPANT_STATUS to update API doc.
    **Allowed for admin user only.**
    """
    db_status = await crud.participant_status.get(db, id=status_id)
    if not db_status:
        raise HTTPException(
            status_code=404,
            detail="A participant status with this id does not exist in the system...",
        )
    if status_in.name and await crud.participant_status.get_by_name(db, status_in.name):
        raise HTTPException(
            status_code=400,
            detail="A participant status with this name already exists in the system...",
        )
    return await crud.participant_status.update(db, db_obj=db_status, obj_in=status_in)
