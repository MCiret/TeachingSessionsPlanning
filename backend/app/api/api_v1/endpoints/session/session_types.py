from typing import Any

from fastapi import APIRouter, Depends, HTTPException  # noqa
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.api import deps

router = APIRouter()


@router.get("/types", response_model=list[schemas.SessionType])
async def read_session_types(
    db: AsyncSession = Depends(deps.get_async_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_admin_user),
) -> Any:
    """
    **Allowed for admin user only.**
    """
    return await crud.session_type.get_multi(db, skip=skip, limit=limit)


@router.post("/type", response_model=schemas.SessionType)
async def create_session_type(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    type_in: schemas.SessionTypeCreate,
    current_user: models.User = Depends(deps.get_current_active_admin_user),
) -> Any:  # * enforce next params te be keyword-only
    """
    **⚠️** Session types are created during prerequisite 'init_db_data' module execution which uses set values
    in SESSION_TYPES list (core/config.py).<br>
    However, if a user would like to create a session type, he has to uncomment this endpoint function
    and update SESSION_TYPES list to update API doc.
    **Allowed for admin user only.**
    """
    if await crud.session_type.get_by_name(db, type_in.name):
        raise HTTPException(
            status_code=400,
            detail="A session type with this name already exists in the system...",
        )
    return await crud.session_type.create(db, obj_in=type_in)


@router.put("/type/{type_id}", response_model=schemas.SessionType)
async def update_session_type_by_id(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    type_id: int,
    type_in: schemas.SessionTypeUpdate,
    current_user: models.User = Depends(deps.get_current_active_admin_user),
) -> Any:  # * enforce next params te be keyword-only
    """
    **⚠️** Session types are created during prerequisite 'init_db_data' module execution which uses set values
    in SESSION_TYPES list (core/config.py).<br>
    However, if a user would like to update a session type, he has to uncomment this endpoint function
    and update SESSION_TYPES list to update API doc.
    **Allowed for admin user only.**
    """
    db_type = await crud.session_type.get(db, id=type_id)
    if not db_type:
        raise HTTPException(
            status_code=404,
            detail="A session type with this id does not exist in the system...",
        )
    if type_in.name and await crud.session_type.get_by_name(db, type_in.name):
        raise HTTPException(
            status_code=400,
            detail="A session type with this name already exists in the system...",
        )
    return await crud.session_type.update(db, db_obj=db_type, obj_in=type_in)
