import pytest
import sys
import os
from unittest.mock import patch, MagicMock, AsyncMock
import json

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))


@pytest.mark.asyncio
async def test_run_conversation_with_tool_calls_iteration():
    """Test run_conversation with multiple rounds of tool calls."""
    import agent
    
    # Save original objects
    original_messages = agent.messages.copy()
    original_chat = agent.chat
    original_process_tool_calls = agent.process_tool_calls
    
    # Set up mocks
    mock_chat = MagicMock()
    
    # Create a series of responses for the conversation flow
    # 1. First response has tool_calls
    response1 = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "I'll help you with that.",
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "function": {
                                "name": "list_files",
                                "arguments": '{"base_dir": "/tmp", "directory": "."}'
                            }
                        }
                    ]
                }
            }
        ]
    }
    
    # 2. Second response has no tool_calls
    response2 = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Here are the files: example.txt"
                }
            }
        ]
    }
    
    try:
        # Replace with our mocks
        agent.chat = mock_chat
        agent.messages = [{"role": "system", "content": agent.system_role}]
        mock_chat.send_messages = AsyncMock(side_effect=[response1, response2])
        agent.process_tool_calls = AsyncMock()
        
        # Patch the input function to handle the chatutil decorator
        with patch('builtins.input', return_value="List the files in my temp directory"):
            with patch('builtins.print'):  # Suppress print output
                # Run the conversation
                result = await agent.run_conversation("List the files in my temp directory")
        
        # Verify process_tool_calls was called
        agent.process_tool_calls.assert_called_once()
        
        # Verify the result
        assert result == "Here are the files: example.txt"
        
    finally:
        # Restore original objects
        agent.messages = original_messages
        agent.chat = original_chat
        agent.process_tool_calls = original_process_tool_calls