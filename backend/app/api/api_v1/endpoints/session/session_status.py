from typing import Any

from fastapi import APIRouter, Depends, HTTPException  # noqa
from sqlalchemy.ext.asyncio import AsyncSession


from app import crud, models, schemas
from app.api import deps

router = APIRouter()


@router.get("/status", response_model=list[schemas.SessionStatus])
async def read_session_status(
    db: AsyncSession = Depends(deps.get_async_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_admin_user),
) -> Any:
    """
    **Allowed for super admin/user only.**
    """
    return await crud.session_status.get_multi(db, skip=skip, limit=limit)


@router.post("/status", response_model=schemas.SessionStatus)
async def create_session_status(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    status_in: schemas.SessionStatusCreate,
    current_user: models.User = Depends(deps.get_current_active_admin_user),
) -> Any:  # * enforce next params te be keyword-only
    """
    **⚠️** Session status are created during prerequisite 'init_db_data' module execution which uses set values
    in SESSION_STATUS list (core/config.py).<br>
    However, if a user would like to create a session status, he has to uncomment this endpoint function
    and update SESSION_STATUS list to update API doc.
    **Allowed for admin user only.**
    """
    if await crud.session_status.get_by_name(db, status_in.name):
        raise HTTPException(
            status_code=400,
            detail="A session status with this name already exists in the system...",
        )
    return await crud.session_status.create(db, obj_in=status_in)


@router.put("/status/{status_id}", response_model=schemas.SessionStatus)
async def update_session_status_by_id(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    status_id: int,
    status_in: schemas.SessionStatusUpdate,
    current_user: models.User = Depends(deps.get_current_active_admin_user),
) -> Any:  # * enforce next params te be keyword-only
    """
    **⚠️** Session status are created during prerequisite 'init_db_data' module execution which uses set values
    in SESSION_STATUS list (core/config.py).<br>
    However, if a user would like to update a session status, he has to uncomment this endpoint function
    and update SESSION_STATUS list to update API doc.
    **Allowed for admin user only.**

    """
    db_status = await crud.session_status.get(db, id=status_id)
    if not db_status:
        raise HTTPException(
            status_code=404,
            detail="A session status with this id does not exist in the system...",
        )
    if status_in.name and await crud.session_status.get_by_name(db, status_in.name):
        raise HTTPException(
            status_code=400,
            detail="A session status with this name already exists in the system...",
        )
    return await crud.session_status.update(db, db_obj=db_status, obj_in=status_in)
