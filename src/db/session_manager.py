from typing import Dict, List, Optional
from datetime import datetime, timezone

from db.schemas import User, Session, Node


class SessionManager:
    def __init__(self, database_client):
        self.database = database_client
        self._hardcoded_user = User(
            username="default_user",
            email="default@ai-agent.local",
            display_name="Default User"
        )

    async def initialize_default_user(self) -> str:
        try:
            self.database.connect()
            query, params = self._hardcoded_user.create()
            self.database._execute(query, params)
            return str(self._hardcoded_user.id)
        except Exception as e:
            print(f"Error initializing default user: {e}")
            return str(self._hardcoded_user.id)
        finally:
            self.database.close()

    async def create_user_session(
        self, 
        title: str = "New Session",
        agent_config: Optional[Dict] = None,
        user_id: Optional[str] = None
    ) -> Session:
        if user_id is None:
            user_id = str(self._hardcoded_user.id)

        session = Session(
            user_id=user_id,
            title=title,
            agent_config=agent_config,
            is_active=True
        )

        try:
            self.database.connect()
            query, params = session.create()
            self.database._execute(query, params)
            
            # Link session to user
            from db.schemas import EdgeType
            link_query, link_params = session.link(
                EdgeType.BELONGS_TO, 
                "USER", 
                user_id
            )
            self.database._execute(link_query, link_params)
            
            return session
        except Exception as e:
            print(f"Error creating session: {e}")
            raise
        finally:
            self.database.close()

    async def get_session(self, session_id: str) -> Optional[Session]:
        try:
            self.database.connect()
            query = f"MATCH (s:SESSION {{id: $session_id}}) RETURN s"
            self.database._execute(query, {"session_id": session_id})
            result = self.database._cur.fetchone()
            
            if result:
                session_data = dict(result[0].properties)
                return Session.from_dict(session_data)
            return None
        except Exception as e:
            print(f"Error getting session: {e}")
            return None
        finally:
            self.database.close()

    async def update_session(
        self, 
        session_id: str, 
        title: Optional[str] = None,
        agent_config: Optional[Dict] = None,
        is_active: Optional[bool] = None
    ) -> bool:
        try:
            self.database.connect()
            
            updates = {"updated_at": datetime.now(timezone.utc).isoformat()}
            if title is not None:
                updates["title"] = title
            if agent_config is not None:
                updates["agent_config"] = agent_config
            if is_active is not None:
                updates["is_active"] = is_active
                
            set_clause = ", ".join([f"s.{key} = ${key}" for key in updates.keys()])
            query = f"MATCH (s:SESSION {{id: $session_id}}) SET {set_clause} RETURN s"
            
            params = {"session_id": session_id, **updates}
            self.database._execute(query, params)
            result = self.database._cur.fetchone()
            
            return result is not None
        except Exception as e:
            print(f"Error updating session: {e}")
            return False
        finally:
            self.database.close()

    async def delete_session(self, session_id: str) -> bool:
        try:
            self.database.connect()
            
            # Delete session and all its relationships
            query = """
            MATCH (s:SESSION {id: $session_id})
            OPTIONAL MATCH (s)-[r]-()
            DELETE r, s
            RETURN count(s) as deleted_count
            """
            
            self.database._execute(query, {"session_id": session_id})
            result = self.database._cur.fetchone()
            
            return result and result[0] > 0
        except Exception as e:
            print(f"Error deleting session: {e}")
            return False
        finally:
            self.database.close()

    async def list_user_sessions(
        self, 
        user_id: Optional[str] = None,
        active_only: bool = True
    ) -> List[Session]:
        if user_id is None:
            user_id = str(self._hardcoded_user.id)

        try:
            self.database.connect()
            
            active_filter = "AND s.is_active = true" if active_only else ""
            query = f"""
            MATCH (s:SESSION)-[:BELONGS_TO]->(u:USER {{id: $user_id}})
            WHERE true {active_filter}
            RETURN s
            ORDER BY s.last_activity DESC
            """
            
            self.database._execute(query, {"user_id": user_id})
            results = self.database._cur.fetchall()
            
            sessions = []
            for result in results:
                session_data = dict(result[0].properties)
                sessions.append(Session.from_dict(session_data))
            
            return sessions
        except Exception as e:
            print(f"Error listing sessions: {e}")
            return []
        finally:
            self.database.close()

    async def update_session_activity(self, session_id: str) -> bool:
        try:
            self.database.connect()
            
            now = datetime.now(timezone.utc).isoformat()
            query = """
            MATCH (s:SESSION {id: $session_id})
            SET s.last_activity = $timestamp, s.updated_at = $timestamp
            RETURN s
            """
            
            self.database._execute(query, {
                "session_id": session_id,
                "timestamp": now
            })
            result = self.database._cur.fetchone()
            
            return result is not None
        except Exception as e:
            print(f"Error updating session activity: {e}")
            return False
        finally:
            self.database.close()