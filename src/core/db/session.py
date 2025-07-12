from typing import Optional

from core.db import (
    get_connection_pool, 
    get_by_id,
    get_by_property,
    delete_by_id
)
from core.db.schemas import Node
from core.db.schemas.session_objects import (
    Session
)

def create_session() -> Session:
    pool = get_connection_pool()
    with pool.get_connection() as db:
        session = Session()
        
        db._execute(*session.create())
        return session
    
def get_session_by_id(session_id: str) -> Optional[Session]:
    return Node.from_dict(
        get_by_id(
            Session,
            session_id
        )
    )

def get_all_sessions() -> list[Session]:
    results = get_by_property(
        Session,
        "is_active",
        True
    )

    if not results:
        return []

    return [Node.from_dict(session) for session in results]

def delete_session(session_id: str) -> None:
    return delete_by_id(
        Session,
        session_id
    )