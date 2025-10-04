import os
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Header, Security, status
from fastapi.security import APIKeyHeader

from core.db.user import get_user_by_token

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
user_token_header = APIKeyHeader(name="X-User-Token", auto_error=False)

def get_api_key(api_key: Annotated[str | None, Security(api_key_header)]) -> str:
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required"
        )
    
    expected_api_key = os.getenv("API_KEY")
    if expected_api_key is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key not configured on server"
        )

    if api_key != expected_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return api_key


def get_user_id(user_token: Annotated[str | None, Security(user_token_header)]) -> Optional[str]:
    if user_token is None:
        return None
    
    user = get_user_by_token(user_token)
    if user is None:
        return None
    
    return user.user_id


def require_user_token(user_token: Annotated[str | None, Security(user_token_header)]) -> str:
    if user_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User token is required"
        )
    
    user = get_user_by_token(user_token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user token"
        )
    
    return user.user_id
