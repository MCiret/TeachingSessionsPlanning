import datetime as dt
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.api import deps
from app.core import security
from app.core.config import settings

router = APIRouter()


@router.post("/login/access-token", response_model=schemas.Token)
async def login_access_token(
    db: AsyncSession = Depends(deps.get_async_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    Token login (OAuth2 compatible) : user login and token access for future requests.
    """
    user = await crud.user.authenticate(
        db, email=form_data.username, api_key=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or api_key")
    elif not await crud.user.is_active(user):
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token_expires = dt.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.post("/login/test-token", response_model=schemas.User)
async def test_token(current_user: models.User = Depends(deps.get_current_user)) -> Any:
    """
    Test access token.
    Depends(deps.get_current_user) is responsible for JWToken checking..
    """
    return current_user
