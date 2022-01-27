from fastapi import APIRouter

from app.api.api_v1.endpoints.user import (
    login, users, admins, speakers
)
from app.api.api_v1.endpoints.user.participant import (
    participants, participant_types, participant_status
)
from app.api.api_v1.endpoints.session import (
    sessions, session_types, session_status
)
from app.api.api_v1.endpoints import availabilities

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(admins.router, prefix="/users", tags=["admins"])
api_router.include_router(speakers.router, prefix="/users", tags=["speakers"])
api_router.include_router(participants.router, prefix="/users/participants", tags=["participants"])
api_router.include_router(participant_types.router, prefix="/users/participants", tags=["participant types & status"])
api_router.include_router(participant_status.router, prefix="/users/participants", tags=["participant types & status"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(session_types.router, prefix="/sessions", tags=["session types & status"])
api_router.include_router(session_status.router, prefix="/sessions", tags=["session types & status"])
api_router.include_router(availabilities.router, prefix="/availabilities", tags=["speaker availabilities"])
