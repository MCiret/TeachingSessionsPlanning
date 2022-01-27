from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.api import deps

router = APIRouter()


@router.get("/admins/", response_model=list[schemas.Admin])
async def read_admins(
    db: AsyncSession = Depends(deps.get_async_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.Admin = Depends(deps.get_current_active_admin_user),
) -> Any:
    """
    Read all admin users in db.
    **Allowed for admin user only.**
    """
    admins = await crud.admin.get_multi(db, skip=skip, limit=limit)
    return admins


@router.post("/admin", response_model=schemas.Admin)
async def create_admin(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    admin_in: schemas.AdminCreate,
    current_user: models.Admin = Depends(deps.get_current_active_admin_user),
) -> Any:
    """
    Create new admin user and send him/her an email.
    **Allowed for admin user only.**
    """
    db_admin = await crud.user.get_by_email(db, email=admin_in.email)
    if db_admin:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists in the system...",
        )
    admin = await crud.admin.create(db, obj_in=admin_in)
    return admin


@router.put("/admin/{admin_id}", response_model=schemas.Admin)
async def update_admin_by_id(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    admin_id: int,
    admin_in: schemas.AdminUpdate,
    current_user: models.User = Depends(deps.get_current_active_admin_user),
) -> Any:
    """
    Update an admin user using id.
    **Allowed for admin user only.**
    """
    if await crud.user.get_by_email(db, email=admin_in.email):
        raise HTTPException(
            status_code=400, detail="A user with this email already exists in the system...")
    db_admin = await crud.admin.get(db, id=admin_id)
    if not db_admin:
        raise HTTPException(
            status_code=404,
            detail="An admin user with this id does not exist in the system...",
        )
    admin = await crud.admin.update(db, db_obj=db_admin, obj_in=admin_in)
    return admin
