from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.api import deps

router = APIRouter()


@router.get("/types", response_model=list[schemas.ParticipantType])
async def read_participant_types(
    db: AsyncSession = Depends(deps.get_async_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_admin_user),
) -> Any:
    """
    **Allowed for admin user only.**
    """
    types = await crud.participant_type.get_multi(db, skip=skip, limit=limit)
    return types


@router.post("/type", response_model=schemas.ParticipantType)
async def create_participant_type(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    type_in: schemas.ParticipantTypeCreate,
    current_user: models.User = Depends(deps.get_current_active_admin_user),
) -> Any:
    """
    **⚠️** Participant types are created during prerequisite 'init_db_data' module execution which uses set values
    in PARTICIPANT_TYPES_NB_SESSION_WEEK dict (core/config.py).<br>
    However, if a user would like to create a participant type, he has to uncomment this endpoint function
    and update PARTICIPANT_TYPES_NB_SESSION_WEEK dict to update API doc.
    **Allowed for admin user only.**
    """
    if await crud.participant_type.get_by_name(db, type_in.name):
        raise HTTPException(
            status_code=400,
            detail="A participant type with this name already exists in the system...",
        )
    type = await crud.participant_type.create(db, obj_in=type_in)
    return type


@router.put("/type/{type_id}", response_model=schemas.ParticipantType)
async def update_participant_type_by_id(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    type_id: int,
    type_in: schemas.ParticipantTypeUpdate,
    current_user: models.User = Depends(deps.get_current_active_admin_user),
) -> Any:
    """
    **⚠️** Participant types are created during prerequisite 'init_db_data' module execution which uses set values
    in PARTICIPANT_TYPES_NB_SESSION_WEEK dict (core/config.py).<br>
    However, if a user would like to update a participant type, he has to uncomment this endpoint function
    and update PARTICIPANT_TYPES_NB_SESSION_WEEK dict to update API doc.
    **Allowed for admin user only.**
    """
    db_type = await crud.participant_type.get(db, id=type_id)
    if not db_type:
        raise HTTPException(
            status_code=404,
            detail="A participant type with this id does not exist in the system...",
        )
    if type_in.name and await crud.participant_type.get_by_name(db, type_in.name):
        raise HTTPException(
            status_code=400,
            detail="A participant type with this name already exists in the system...",
        )
    type = await crud.participant_type.update(db, db_obj=db_type, obj_in=type_in)
    return type
