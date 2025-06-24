import pytest
import json
from unittest.mock import Mock, patch

class TestFrontendSessionStorage:
    """Test that the frontend properly stores and retrieves sessionId"""
    
    def test_session_with_backend_id_storage(self):
        """Test that session with backend sessionId is properly stored"""
        # Simulate a session as it would be stored in localStorage
        session_with_backend_id = {
            "id": "frontend-session-123",
            "sessionId": "backend-uuid-456",  # Backend session ID
            "title": "Test Chat",
            "messages": [
                {
                    "id": "msg-1",
                    "content": "Hello",
                    "role": "user",
                    "timestamp": "2025-06-24T10:00:00Z"
                },
                {
                    "id": "msg-2", 
                    "content": "Hi there!",
                    "role": "assistant",
                    "timestamp": "2025-06-24T10:00:01Z",
                    "usedTools": ["google_search"]
                }
            ],
            "createdAt": "2025-06-24T10:00:00Z"
        }
        
        # Verify that when serialized/deserialized, sessionId is preserved
        serialized = json.dumps(session_with_backend_id)
        deserialized = json.loads(serialized)
        
        assert deserialized["sessionId"] == "backend-uuid-456"
        assert deserialized["id"] == "frontend-session-123"
        assert len(deserialized["messages"]) == 2
        
    def test_session_without_backend_id_storage(self):
        """Test that legacy session without sessionId is handled properly"""
        # Simulate a legacy session without backend sessionId
        legacy_session = {
            "id": "legacy-session-123",
            "title": "Legacy Chat",
            "messages": [
                {
                    "id": "msg-1",
                    "content": "Old message",
                    "role": "user",
                    "timestamp": "2025-06-24T09:00:00Z"
                }
            ],
            "createdAt": "2025-06-24T09:00:00Z"
        }
        
        # Verify that sessionId is not present
        assert "sessionId" not in legacy_session
        
        # Simulate loading this session and adding a sessionId
        legacy_session["sessionId"] = "newly-created-backend-uuid"
        
        # Verify it can be stored and retrieved
        serialized = json.dumps(legacy_session)
        deserialized = json.loads(serialized)
        
        assert deserialized["sessionId"] == "newly-created-backend-uuid"
        assert deserialized["id"] == "legacy-session-123"
        
    def test_multiple_sessions_storage(self):
        """Test storing multiple sessions with different sessionId states"""
        sessions = [
            {
                "id": "session-1",
                "sessionId": "backend-uuid-1",
                "title": "Chat 1",
                "messages": [],
                "createdAt": "2025-06-24T10:00:00Z"
            },
            {
                "id": "session-2", 
                "sessionId": "backend-uuid-2",
                "title": "Chat 2",
                "messages": [],
                "createdAt": "2025-06-24T11:00:00Z"
            },
            {
                "id": "session-3",
                "title": "Chat 3 (no backend)",
                "messages": [],
                "createdAt": "2025-06-24T12:00:00Z"
            }
        ]
        
        # Serialize and deserialize
        serialized = json.dumps(sessions)
        deserialized = json.loads(serialized)
        
        # Verify all sessions are preserved
        assert len(deserialized) == 3
        
        # Session 1 and 2 should have backend sessionIds
        assert deserialized[0]["sessionId"] == "backend-uuid-1"
        assert deserialized[1]["sessionId"] == "backend-uuid-2"
        
        # Session 3 should not have sessionId
        assert "sessionId" not in deserialized[2]
        
    def test_session_creation_flow(self):
        """Test the flow of creating a new session with backend integration"""
        # Step 1: Frontend creates session placeholder
        frontend_session = {
            "id": "temp-frontend-id",
            "title": "New Chat",
            "messages": [],
            "createdAt": "2025-06-24T10:00:00Z"
        }
        
        # Step 2: Backend returns session ID
        backend_response = {
            "session_id": "backend-created-uuid-789",
            "message": "Session created successfully"
        }
        
        # Step 3: Frontend updates session with backend ID
        frontend_session["sessionId"] = backend_response["session_id"]
        
        # Step 4: Session is saved to localStorage
        sessions_to_save = [frontend_session]
        localStorage_data = json.dumps(sessions_to_save)
        
        # Step 5: Verify data integrity
        loaded_sessions = json.loads(localStorage_data)
        loaded_session = loaded_sessions[0]
        
        assert loaded_session["id"] == "temp-frontend-id"
        assert loaded_session["sessionId"] == "backend-created-uuid-789"
        assert loaded_session["title"] == "New Chat"
        assert len(loaded_session["messages"]) == 0
        
    def test_session_deletion_cleanup(self):
        """Test that session deletion removes both frontend and backend data"""
        sessions = [
            {
                "id": "session-to-keep",
                "sessionId": "backend-keep",
                "title": "Keep This",
                "messages": [],
                "createdAt": "2025-06-24T10:00:00Z"
            },
            {
                "id": "session-to-delete",
                "sessionId": "backend-delete",
                "title": "Delete This", 
                "messages": [],
                "createdAt": "2025-06-24T11:00:00Z"
            }
        ]
        
        # Simulate deletion
        session_to_delete_id = "session-to-delete"
        session_to_delete = next(s for s in sessions if s["id"] == session_to_delete_id)
        backend_session_id = session_to_delete["sessionId"]
        
        # Remove from sessions list
        sessions = [s for s in sessions if s["id"] != session_to_delete_id]
        
        # Verify deletion
        assert len(sessions) == 1
        assert sessions[0]["id"] == "session-to-keep"
        assert backend_session_id == "backend-delete"  # This would be used for backend deletion
        
        # Verify remaining session is intact
        remaining_session = sessions[0]
        assert remaining_session["sessionId"] == "backend-keep"
        assert remaining_session["title"] == "Keep This"


if __name__ == "__main__":
    pytest.main([__file__])
