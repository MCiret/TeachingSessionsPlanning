import datetime as dt
from typing import Any
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.utils.email_utils import send_reset_api_key_email
from app.api import deps
from app.core import security
from app.core.config import settings, jinja_templates


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
async def test_token(current_user: models.User = Depends(deps.check_jwt_and_get_current_user)) -> Any:
    """
    Test access token.
    """
    return current_user


@router.post("/login/recover-api-key/{email}")
async def recover_api_key(email: str, db: AsyncSession = Depends(deps.get_async_db)) -> Any:
    """
    Recover your API Key by receiving an email containing a temporary link to follow.
    """
    user = await crud.user.get_by_email(db, email=email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system...",
        )
    api_key_reset_token = security.generate_api_key_reset_token(email=email)
    send_reset_api_key_email(
        email_to=email, token=api_key_reset_token
    )
    return {"msg": "Password recovery email sent"}


# https://fastapi.tiangolo.com/advanced/templates/#using-jinja2templates
@router.get("/login/reset-api-key-form", response_class=HTMLResponse)
async def reset_api_key_form(request: Request, email: str, token: str) -> HTMLResponse:
    """
    Choose your new API Key (first use endpoint /login/recover-api-key/{email} to receive a link by email).
    """
    return jinja_templates.TemplateResponse(
        "reset_api_key_form.html",
        {
            "request": request,
            "email_to": email,
            "token": token,
            "project_name": settings.PROJECT_NAME
        }
    )


@router.post("/login/reset-api-key/")
async def reset_api_key(
    new_api_key: str = Form(...),
    apikey_reset_token: str = Form(...),
    db: AsyncSession = Depends(deps.get_async_db),
) -> Any:
    """
    Reset API Key.
    First, use the endpoint /login/recover-api-key/{email} to receive a link (containing the token) by email.
    """
    email = security.verify_api_key_reset_token(apikey_reset_token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")
    user = await crud.user.get_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system...",
        )
    elif not await crud.user.is_active(user):
        raise HTTPException(status_code=400, detail="Inactive user")
    hashed_api_key = security.get_password_hash(new_api_key)
    user.hashed_api_key = hashed_api_key
    db.add(user)
    await db.commit()
    return {"msg": "Password updated successfully"}
