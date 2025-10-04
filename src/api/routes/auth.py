from fastapi import APIRouter, HTTPException, Header
from typing import Annotated, Optional

from api.models import (
    LoginRequest,
    LoginResponse,
    UserSessionsResponse,
    SessionInfo,
)
from core.db.user import validate_user_token, get_user_by_token
from core.db.session import get_all_sessions

router = APIRouter(prefix="/api/auth")


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> LoginResponse:
    user = validate_user_token(request.user_token)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid user token"
        )
    
    return LoginResponse(
        user_id=user.user_id,
        user_token=user.user_token,
        email=getattr(user, "email", None),
        name=getattr(user, "name", None),
        message="Login successful"
    )


@router.get("/sessions", response_model=UserSessionsResponse)
async def get_user_sessions(
    user_token: Annotated[str, Header(alias="X-User-Token")]
) -> UserSessionsResponse:
    user = get_user_by_token(user_token)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid user token"
        )
    
    sessions = get_all_sessions(user_id=user.user_id)
    session_infos = [
        SessionInfo(
            session_id=str(session.session_id),
            title=session.title,
            last_activity=session.last_activity.isoformat(),
            conversation_count=session.conversation_count,
            is_active=session.is_active,
        )
        for session in sessions
    ]
    
    return UserSessionsResponse(
        user_id=user.user_id,
        sessions=session_infos
    )
