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
    status = await crud.participant_status.get_multi(db, skip=skip, limit=limit)
    return status


@router.post("/status", response_model=schemas.ParticipantStatus)
async def create_participant_status(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    status_in: schemas.ParticipantStatusCreate,
    current_user: models.User = Depends(deps.get_current_active_admin_user),
) -> Any:
    """
    **⚠️** Participant status are created in initialize_db() function by running execution of the init_db_data module
    (prerequisite step before running this app).<br>
    However, if a user would like to create (or update, see below), he has to uncomment this function.
    A user who would use this function should update PARTICIPANT_STATUS list in core/config.py.
    **Allowed for admin user only.**
    """
    if await crud.participant_status.get_by_name(db, name=status_in.name):
        raise HTTPException(
            status_code=400,
            detail="A participant status with this name already exists in the system...",
        )
    status = await crud.participant_status.create(db, obj_in=status_in)
    return status


@router.put("/status/{status_id}", response_model=schemas.ParticipantStatus)
async def update_participant_status_by_id(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    status_id: int,
    status_in: schemas.ParticipantStatusUpdate,
    current_user: models.User = Depends(deps.get_current_active_admin_user),
) -> Any:
    """
    **⚠️** Participant status are created in initialize_db() function by running execution of the init_db_data module
    (prerequisite step before running this app).<br>
    However, if a user would like to update (or create, see above), he has to uncomment this function.
    A user who would use this function should update PARTICIPANT_STATUS list in core/config.py.
    **Allowed for admin user only.**
    """
    db_status = await crud.participant_status.get(db, id=status_id)
    if not db_status:
        raise HTTPException(
            status_code=404,
            detail="A participant status with this id does not exist in the system...",
        )
    if status_in.name and await crud.participant_status.get_by_name(db, name=status_in.name):
        raise HTTPException(
            status_code=400,
            detail="A participant status with this name already exists in the system...",
        )
    status = await crud.participant_status.update(db, db_obj=db_status, obj_in=status_in)
    return status
