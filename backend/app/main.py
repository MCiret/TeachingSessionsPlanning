from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from app.api.api_v1.api import api_router
from app.core.config import settings

tags_metadata = [
    {
        "name": "login",
        "description": "",
    },
    {
        "name": "users",
        "description": "Operations with all kind of users (i.e Admin, Speaker and Participant). "
                       "**Allowed for super/admin user only.**"
                       "<br>ℹ️ **User creation is not possible.** You have to create an Admin, "
                       "a Speaker or a Participant using their specific tagged operations.",
    },
    {
        "name": "admins",
        "description": "",
    },
    {
        "name": "speakers",
        "description": "",
    },
    {
        "name": "participants",
        "description": "",
    },
    {
        "name": "participant types & status",
        "description": "Mainly for reading participant types and status that exist in db. "
                       "<br>ℹ️ *For creating/updating, uncomment endpoints in source code...*",
    },
    {
        "name": "sessions",
        "description": "",
    },
    {
        "name": "session types & status",
        "description": "Mainly for reading session types and status that exist in db. "
                       "<br>ℹ️ *For creating/updating, uncomment endpoints in source code...*",
    },
]

""" Run the init_db_data.py to create a super user before launching the main app."""
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    openapi_tags=tags_metadata
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.mount(settings.STATIC_DIR, StaticFiles(directory="app/static"), name='static')
app.include_router(api_router, prefix=settings.API_V1_STR)
