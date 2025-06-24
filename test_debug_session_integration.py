#!/usr/bin/env python3
"""
Test script to verify debug capture works with session ID for agent-to-model and model-to-agent events.
"""

import os
import asyncio
from unittest.mock import Mock, patch
from core.debug_capture import get_debug_capture_instance, DebugEventType
from core.llm.chat import Chat
from core.llm.client import ChatClient
from tools import Tool

class MockTool(Tool):
    def __init__(self):
        super().__init__(
            name="mock_tool",
            description="A mock tool for testing",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Test query"}
                },
                "required": ["query"]
            }
        )
    
    async def run(self, query: str):
        return {"result": f"Mock result for: {query}"}

async def test_debug_capture_integration():
    print("Testing debug capture integration with session ID...")
    
    # Set up environment variables for testing
    os.environ["AZURE_OPENAI_API_KEY"] = "test_key"
    os.environ["AZURE_OPENAI_CHAT_MODEL"] = "test_model"
    os.environ["AZURE_OPENAI_CHAT_ENDPOINT"] = "https://test.endpoint.com"
    
    session_id = "test_session_123"
    
    # Create debug capture instance and enable it
    debug_capture = get_debug_capture_instance(session_id)
    debug_capture.enable()
    
    # Create a chat instance with the session ID
    chat = Chat(tool_list=[MockTool()], session_id=session_id)
    
    # Verify that the chat client has the correct session ID
    assert chat.chat_client.session_id == session_id
    print(f"✓ Chat client initialized with session ID: {session_id}")
    
    # Mock the HTTP response for testing
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Hello! This is a test response."
                }
            }
        ]
    }
    
    # Test the LLM request and response capture
    with patch.object(chat.chat_client.http_client, 'post', return_value=mock_response):
        messages = [{"role": "user", "content": "Hello, test message"}]
        
        # This should trigger both capture_llm_request and capture_llm_response
        response = await chat.send_messages(messages)
        
        # Verify the response
        assert response is not None
        print("✓ Mock LLM request completed successfully")
    
    # Check the captured events
    events = debug_capture.get_events()
    
    # Should have captured both request and response
    assert len(events) >= 2, f"Expected at least 2 events, got {len(events)}"
    
    # Find the agent-to-model event
    request_events = [e for e in events if e["event_type"] == DebugEventType.AGENT_TO_MODEL]
    response_events = [e for e in events if e["event_type"] == DebugEventType.MODEL_TO_AGENT]
    
    assert len(request_events) >= 1, f"Expected at least 1 request event, got {len(request_events)}"
    assert len(response_events) >= 1, f"Expected at least 1 response event, got {len(response_events)}"
    
    # Verify the request event
    request_event = request_events[0]
    assert request_event["session_id"] == session_id
    assert request_event["message"] == "LLM Request"
    assert "payload" in request_event["data"]
    assert "messages" in request_event["data"]["payload"]
    print("✓ Agent-to-model event captured correctly")
    
    # Verify the response event
    response_event = response_events[0]
    assert response_event["session_id"] == session_id
    assert response_event["message"] == "LLM Response"
    assert "response" in response_event["data"]
    assert "choices" in response_event["data"]["response"]
    print("✓ Model-to-agent event captured correctly")
    
    print("✓ All tests passed! Debug capture is working correctly with session IDs.")
    return True

if __name__ == "__main__":
    result = asyncio.run(test_debug_capture_integration())
    if result:
        print("\n🎉 Integration test completed successfully!")
    else:
        print("\n❌ Integration test failed!")
        exit(1)
