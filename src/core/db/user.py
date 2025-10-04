from typing import Optional

from core.db import get_connection_pool, get_by_property
from core.db.schemas.user import User


def get_or_create_user(user_token: str, email: Optional[str] = None, name: Optional[str] = None) -> User:
    result = get_by_property(User, "user_token", user_token, fetch_one=True)
    
    if result:
        return User.from_dict(result)
    
    user = User(user_token=user_token, email=email, name=name)
    pool = get_connection_pool()
    with pool.get_connection() as db:
        db._execute(*user.create())
    return user


def validate_user_token(user_token: str) -> Optional[User]:
    try:
        user = get_or_create_user(user_token)
        user.update_last_login()
        pool = get_connection_pool()
        with pool.get_connection() as db:
            q = f"MATCH (n:`{User.label()}` {{user_token: $user_token}}) SET n += $props RETURN n"
            props = user.to_dict()
            db._execute(q, {"user_token": user_token, "props": props})
        return user
    except Exception:
        return None


def get_user_by_token(user_token: str) -> Optional[User]:
    result = get_by_property(User, "user_token", user_token, fetch_one=True)
    
    if result:
        return User.from_dict(result)
    
    return None
