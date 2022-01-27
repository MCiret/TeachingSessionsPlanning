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
    **Allowed for super user only.**
    """
    types = await crud.session_type.get_multi(db, skip=skip, limit=limit)
    return types


# @router.post("/type", response_model=schemas.SessionType)
# async def create_session_type(
#     *,
#     db: AsyncSession = Depends(deps.get_async_db),
#     type_in: schemas.SessionTypeCreate,
#     current_user: models.User = Depends(deps.get_current_active_admin_user),
# ) -> Any:  # * enforce next params te be keyword-only
#     """
#     **⚠️** Session types are created in initialize_db() function by running execution of the init_db_data module
#     (prerequisite step before running this app).<br>
#     However, if a user would like to create (or update, see below), he has to uncomment this function.
#     A user who would use this function should update SESSION_TYPES list in core/config.py.
#     **Allowed for super user only.**
#     """
#     try:
#         type = await crud.session_type.create(db, obj_in=type_in)
#     except IntegrityError:
#         raise HTTPException(
#             status_code=400,
#             detail="A session type with this name already exists in the system...",
#         )
#     return type


# @router.put("/type/{type_id}", response_model=schemas.SessionType)
# async def update_session_types(
#     *,
#     db: AsyncSession = Depends(deps.get_async_db),
#     type_id: int,
#     type_in: schemas.SessionTypeUpdate,
#     current_user: models.User = Depends(deps.get_current_active_admin_user),
# ) -> Any:  # * enforce next params te be keyword-only
#     """
#     **⚠️** Session types are created in initialize_db() function by running execution of the init_db_data module
#     (prerequisite step before running this app).<br>
#     However, if a user would like to update (or create, see above), he has to uncomment this function.
#     A user who would use this function should update SESSION_TYPES list in core/config.py.
#     **Allowed for super user only.**
#     """
#     db_type = await crud.session_type.get(db, id=type_id)
#     if not db_type:
#         raise HTTPException(
#             status_code=404,
#             detail="A session type with this id does not exist in the system...",
#         )
#     type = await crud.session_type.update(db, db_obj=db_type, obj_in=type_in)
#     return type
