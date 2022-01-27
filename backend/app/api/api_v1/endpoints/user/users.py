from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic.networks import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.api import deps
from app.core.config import settings

router = APIRouter()


@router.get("/all/", response_model=list[schemas.User])
async def read_all_users(
    db: AsyncSession = Depends(deps.get_async_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_admin_user),
) -> Any:
    """
    Read all users in db.
    Returns only users (base table) common fields.
    **Allowed for admin user only.**
    """
    users = await crud.user.get_multi(db, skip=skip, limit=limit)
    return users


@router.get("/me", response_model=schemas.User)
async def read_user_me(
    db: AsyncSession = Depends(deps.get_async_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current user. Returns all specific fields according to the profile
    (i.e the "subtable" : Admin, Speaker or Participant).
    """
    return current_user


@router.put("/me", response_model=schemas.User)
async def update_user_me(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    api_key: str = Body(None),
    first_name: str = Body(None),
    last_name: str = Body(None),
    email: EmailStr = Body(None),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update own user. Only all users common fields could be modified : api key, first/last name and email.
    """
    current_user_data = jsonable_encoder(current_user)
    user_in = schemas.UserUpdate(**current_user_data)
    if api_key is not None:
        user_in.api_key = api_key
    if first_name is not None:
        user_in.first_name = first_name
    if last_name is not None:
        user_in.last_name = last_name
    if email is not None:
        if await crud.user.get_by_email(db, email=email):
            raise HTTPException(status_code=400, detail="A user with this email already exists in the system...")
        user_in.email = email
    user = await crud.user.update(db, db_obj=current_user, obj_in=user_in)
    return user


@router.get("/{user_id}", response_model=schemas.User)
async def read_user_by_id(
    user_id: int,
    current_user: models.User = Depends(deps.get_current_active_admin_user),
    db: AsyncSession = Depends(deps.get_async_db),
) -> Any:
    """
    Get a specific user by id.
    Returns only user (base table) common fields.
    **Allowed for admin user only.**
    """
    return await crud.user.get(db, id=user_id)


@router.post("/open", response_model=schemas.User)
async def create_user_open(
    *,
    db: AsyncSession = Depends(deps.get_async_db),
    api_key: str = Body(...),
    email: EmailStr = Body(...),
    first_name: str = Body(None),
    last_name: str = Body(None),
) -> Any:
    """
    Create new user without the need to be logged in.
    Allowed only if settings.USERS_OPEN_REGISTRATION is set to True (i.e only for development...).
    """
    if not settings.USERS_OPEN_REGISTRATION:  # set to True (core/config.py) ONLY for development..
        raise HTTPException(
            status_code=403,
            detail="Open user registration is forbidden on this server",
        )
    user = await crud.user.get_by_email(db, email=email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system",
        )
    user_in = schemas.UserCreate(api_key=api_key, email=email, first_name=first_name, last_name=last_name)
    user = await crud.user.create(db, obj_in=user_in)
    return user
