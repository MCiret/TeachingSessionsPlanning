from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.core import security
from app.core.config import settings
from app.db.db_session import AsyncSessionLocal

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


async def get_async_db():
    async with AsyncSessionLocal() as async_session:
        yield async_session


async def check_jwt_and_get_current_user(
    db: AsyncSession = Depends(get_async_db), token: str = Depends(reusable_oauth2)
) -> models.User:
    """
    Checks if token is valid and return the current logged user if OK.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = schemas.TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = await crud.user.get(db, id=token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


async def get_current_active_user(
    current_user: models.User = Depends(check_jwt_and_get_current_user),
) -> models.User:
    if not await crud.user.is_active(current_user):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_active_speaker_or_admin_user(
    current_user: models.User = Depends(get_current_active_user),
) -> models.User:
    if not await crud.user.is_speaker(current_user) and not await crud.user.is_admin(current_user):
        raise HTTPException(status_code=400, detail="To do this, the user has to be a Speaker or Admin user")
    return current_user


async def get_current_active_speaker_or_participant_user(
    current_user: models.User = Depends(get_current_active_user),
) -> models.User:
    if not await crud.user.is_speaker(current_user) and not await crud.user.is_participant(current_user):
        raise HTTPException(status_code=400, detail="To do this, the user has to be a Speaker or Participant user")
    return current_user


async def get_current_active_admin_user(
    current_user: models.User = Depends(check_jwt_and_get_current_user),
) -> models.User:
    if not await crud.user.is_admin(current_user):
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user


async def get_current_active_speaker_user(
    current_user: models.User = Depends(check_jwt_and_get_current_user),
) -> models.User:
    if not await crud.user.is_speaker(current_user):
        raise HTTPException(
            status_code=400, detail="To do this, the user has to be a Speaker user"
        )
    return current_user
