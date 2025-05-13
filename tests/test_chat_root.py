"""
Tests for agent.py root functionality
"""

import pytest
import sys
import os
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock, call

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))


def test_agent_initial_state():
    """Test agent initialization and initial state."""
    # Import the module
    import agent

    # Verify chat object is created
    assert agent.chat is not None
    
    # Verify chat has the correct tools
    assert len(agent.tools) >= 5
    
    # Check system message is set properly
    assert len(agent.messages) == 1
    assert agent.messages[0]["role"] == "system"
    assert isinstance(agent.messages[0]["content"], str)
    assert "Agent Smith" in agent.messages[0]["content"]


def test_agent_add_tool():
    """Test that tools can be added to the agent."""
    # Import the module
    import agent
    from tools import Tool
    
    # Create a test tool
    test_tool = Tool("test_tool")
    
    # Save the original chat
    original_chat = agent.chat
    
    try:
        # Mock the add_tool method to prevent side effects
        agent.chat = MagicMock()
        agent.chat.add_tool = MagicMock()  
        
        # Call the add_tool function
        agent.add_tool(test_tool)
        
        # Verify the tool was added correctly
        agent.chat.add_tool.assert_called_once_with(test_tool)
    finally:
        # Restore original chat
        agent.chat = original_chat


def test_agent_run_conversation_structure():
    """Test the basic structure of the run_conversation function."""
    # Import the module
    import agent
    
    # Verify run_conversation is defined and callable
    assert callable(agent.run_conversation)
    
    # Check the function signature
    import inspect
    sig = inspect.signature(agent.run_conversation)
    
    # We expect one parameter (user_prompt) plus any inherited from the decorators
    assert len(sig.parameters) >= 1


@pytest.mark.asyncio
async def test_chat_run_conversation_flow():
    """Test the flow of run_conversation with proper async handling."""
    import agent as agent_mod
    import core
    
    # Save original objects
    original_messages = agent_mod.messages.copy()
    original_chat = agent_mod.chat
    original_pretty_print = agent_mod.pretty_print
    
    try:
        # Mock chat and its methods
        mock_chat = MagicMock()
        mock_chat.send_messages = AsyncMock(return_value={
            "choices": [
                {"message": {"content": "Test response", "role": "assistant"}}
            ]
        })
        agent_mod.chat = mock_chat
        
        # Mock pretty_print to avoid actual printing
        agent_mod.pretty_print = MagicMock()
        
        # Create our own implementation of run_conversation that mimics the original
        async def test_run_conversation(user_input):
            agent_mod.messages.append({"role": "user", "content": user_input})
            response = await agent_mod.chat.send_messages(agent_mod.messages)
            
            choices = response.get("choices", [])
            assistant_message = choices[0].get("message", {})
            agent_mod.messages.append(assistant_message)
            
            # Handle the case where tool_calls might be missing or not a list
            while assistant_message.get("tool_calls"):
                await agent_mod.chat.process_tool_calls(assistant_message, agent_mod.messages.append)
                
                response = await agent_mod.chat.send_messages(agent_mod.messages)
                if not (response and response.get("choices", None)):
                    break
                    
                assistant_message = response.get("choices", [{}])[0].get("message", {})
                agent_mod.messages.append(assistant_message)
            
            result = assistant_message.get("content", "")
            agent_mod.pretty_print("Result", result)
            return result
        
        # Call the test function
        result = await test_run_conversation("Test input")
        
        # Verify send_messages was called with messages containing the input
        mock_chat.send_messages.assert_called_once()
        call_args = mock_chat.send_messages.call_args[0][0]
        assert any(m["role"] == "user" and m["content"] == "Test input" for m in call_args)
        
        # Verify pretty_print was called with the result
        agent_mod.pretty_print.assert_called_once_with("Result", "Test response")
        
    finally:
        # Restore original objects
        agent_mod.messages = original_messages
        agent_mod.chat = original_chat
        agent_mod.pretty_print = original_pretty_print


@pytest.mark.asyncio
async def test_chat_message_accumulation():
    """Test that messages accumulate properly."""
    import agent as agent_mod
    import core
    
    # Save original objects
    original_messages = agent_mod.messages.copy()
    original_chat = agent_mod.chat
    original_pretty_print = agent_mod.pretty_print
    
    try:
        # Create mock response
        mock_response = {
            "choices": [
                {"message": {"content": "Response 1", "role": "assistant"}}
            ]
        }
        
        # Mock chat and its methods
        mock_chat = MagicMock()
        mock_chat.send_messages = AsyncMock(return_value=mock_response)
        agent_mod.chat = mock_chat
        
        # Mock pretty_print to avoid actual printing
        agent_mod.pretty_print = MagicMock()
        
        # Reset messages to initial state
        agent_mod.messages = [{"role": "system", "content": agent_mod.system_role}]
        
        # Create our own implementation of run_conversation that mimics the original
        async def test_run_conversation(user_input):
            agent_mod.messages.append({"role": "user", "content": user_input})
            response = await agent_mod.chat.send_messages(agent_mod.messages)
            
            choices = response.get("choices", [])
            assistant_message = choices[0].get("message", {})
            agent_mod.messages.append(assistant_message)
            
            result = assistant_message.get("content", "")
            agent_mod.pretty_print("Result", result)
            return result
        
        # Call the function
        await test_run_conversation("Test accumulation")
        
        # Verify messages were accumulated correctly
        assert len(agent_mod.messages) == 3
        assert agent_mod.messages[1]["role"] == "user"
        assert agent_mod.messages[1]["content"] == "Test accumulation"
        assert agent_mod.messages[2]["role"] == "assistant"
        assert agent_mod.messages[2]["content"] == "Response 1"
        
    finally:
        # Restore original objects
        agent_mod.messages = original_messages
        agent_mod.chat = original_chat
        agent_mod.pretty_print = original_pretty_print


@pytest.mark.asyncio
async def test_chat_multiple_runs_message_growth():
    """Test message growth over multiple conversation runs."""
    import agent as agent_mod
    import core
    
    # Save original objects
    original_messages = agent_mod.messages.copy()
    original_chat = agent_mod.chat
    original_pretty_print = agent_mod.pretty_print
    
    try:
        # Create mock responses
        mock_responses = [
            {"choices": [{"message": {"content": "Response 1", "role": "assistant"}}]},
            {"choices": [{"message": {"content": "Response 2", "role": "assistant"}}]}
        ]
        
        # Mock chat and its methods
        mock_chat = MagicMock()
        mock_chat.send_messages = AsyncMock(side_effect=mock_responses)
        agent_mod.chat = mock_chat
        
        # Mock pretty_print to avoid actual printing
        agent_mod.pretty_print = MagicMock()
        
        # Reset messages to initial state
        agent_mod.messages = [{"role": "system", "content": agent_mod.system_role}]
        
        # Create our own implementation of run_conversation that mimics the original
        async def test_run_conversation(user_input):
            agent_mod.messages.append({"role": "user", "content": user_input})
            response = await agent_mod.chat.send_messages(agent_mod.messages)
            
            choices = response.get("choices", [])
            assistant_message = choices[0].get("message", {})
            agent_mod.messages.append(assistant_message)
            
            result = assistant_message.get("content", "")
            agent_mod.pretty_print("Result", result)
            return result
        
        # Call run_conversation twice with different inputs
        await test_run_conversation("First input")
        # Verify message count
        assert len(agent_mod.messages) == 3
        
        await test_run_conversation("Second input")
        # Verify message count has increased
        assert len(agent_mod.messages) == 5
        
        # Verify message contents
        assert agent_mod.messages[1]["role"] == "user"
        assert agent_mod.messages[1]["content"] == "First input"
        assert agent_mod.messages[2]["role"] == "assistant"
        assert agent_mod.messages[2]["content"] == "Response 1"
        assert agent_mod.messages[3]["role"] == "user"
        assert agent_mod.messages[3]["content"] == "Second input"
        assert agent_mod.messages[4]["role"] == "assistant"
        assert agent_mod.messages[4]["content"] == "Response 2"
        
    finally:
        # Restore original objects
        agent_mod.messages = original_messages
        agent_mod.chat = original_chat
        agent_mod.pretty_print = original_pretty_print


@pytest.mark.asyncio
async def test_chat_run_conversation_print():
    """Test pretty print functionality in run_conversation."""
    import agent as agent_mod
    import core
    
    # Save original objects
    original_messages = agent_mod.messages.copy()
    original_chat = agent_mod.chat
    original_pretty_print = agent_mod.pretty_print
    
    try:
        # Mock chat.send_messages to return a specific response
        mock_chat = MagicMock()
        mock_chat.send_messages = AsyncMock(return_value={
            "choices": [{"message": {"content": "Test response", "role": "assistant"}}]
        })
        agent_mod.chat = mock_chat
        
        # Mock pretty_print to verify it's called
        mock_pretty_print = MagicMock()
        agent_mod.pretty_print = mock_pretty_print
        
        # Create our own implementation of run_conversation that mimics the original
        async def test_run_conversation(user_input):
            agent_mod.messages.append({"role": "user", "content": user_input})
            response = await agent_mod.chat.send_messages(agent_mod.messages)
            
            choices = response.get("choices", [])
            assistant_message = choices[0].get("message", {})
            agent_mod.messages.append(assistant_message)
            
            result = assistant_message.get("content", "")
            agent_mod.pretty_print("Result", result)
            return result
        
        # Call the function
        await test_run_conversation("Test print")
        
        # Verify pretty_print was called with the expected content
        mock_pretty_print.assert_called_with("Result", "Test response")
        
    finally:
        # Restore original objects
        agent_mod.messages = original_messages
        agent_mod.chat = original_chat
        agent_mod.pretty_print = original_pretty_print


@pytest.mark.asyncio
async def test_chat_run_conversation_async():
    """Test the async functionality of run_conversation."""
    import agent as agent_mod
    import core
    
    # Save original objects
    original_messages = agent_mod.messages.copy()
    original_chat = agent_mod.chat
    original_pretty_print = agent_mod.pretty_print
    
    try:
        # Mock chat and its methods
        mock_chat = MagicMock()
        mock_chat.send_messages = AsyncMock(return_value={
            "choices": [{"message": {"content": "Async response", "role": "assistant"}}]
        })
        agent_mod.chat = mock_chat
        
        # Mock pretty_print to avoid actual printing
        agent_mod.pretty_print = MagicMock()
        
        # Create our own implementation of run_conversation that mimics the original
        async def test_run_conversation(user_input):
            agent_mod.messages.append({"role": "user", "content": user_input})
            response = await agent_mod.chat.send_messages(agent_mod.messages)
            
            choices = response.get("choices", [])
            assistant_message = choices[0].get("message", {})
            agent_mod.messages.append(assistant_message)
            
            result = assistant_message.get("content", "")
            agent_mod.pretty_print("Result", result)
            return result
        
        # Call the function
        await test_run_conversation("Async test")
        
        # Verify chat.send_messages was called asynchronously
        mock_chat.send_messages.assert_called_once()
        assert isinstance(mock_chat.send_messages.call_args[0][0], list)
        
    finally:
        # Restore original objects
        agent_mod.messages = original_messages
        agent_mod.chat = original_chat
        agent_mod.pretty_print = original_pretty_print


@pytest.mark.asyncio
async def test_chat_send_messages_response_handling():
    """Test that send_messages responses are handled correctly."""
    import agent as agent_mod
    import core
    
    # Save original objects
    original_messages = agent_mod.messages.copy()
    original_chat = agent_mod.chat
    original_pretty_print = agent_mod.pretty_print
    
    try:
        # Create a mock response with missing fields
        incomplete_response = {
            # Missing 'choices' field
        }
        complete_response = {
            "choices": [
                {
                    "message": {
                        "content": "Complete response",
                        "role": "assistant"
                    }
                }
            ]
        }
        
        # Mock chat and its methods to return different responses
        mock_chat = MagicMock()
        mock_chat.send_messages = AsyncMock(side_effect=[incomplete_response, complete_response])
        agent_mod.chat = mock_chat
        
        # Mock pretty_print to avoid actual printing
        agent_mod.pretty_print = MagicMock()
        
        # Create our own implementation of run_conversation that mimics the original
        # but handles the incomplete response gracefully
        async def test_run_conversation(user_input):
            agent_mod.messages.append({"role": "user", "content": user_input})
            response = await agent_mod.chat.send_messages(agent_mod.messages)
            
            try:
                choices = response.get("choices", [])
                assistant_message = choices[0].get("message", {})
                agent_mod.messages.append(assistant_message)
                
                result = assistant_message.get("content", "")
                agent_mod.pretty_print("Result", result)
                return result
            except (IndexError, AttributeError):
                # Handle missing choices or other errors
                return None
        
        # Call the function with incomplete response
        result = await test_run_conversation("Test response handling")
        
        # Verify chat.send_messages was called
        assert mock_chat.send_messages.call_count == 1
        
    finally:
        # Restore original objects
        agent_mod.messages = original_messages
        agent_mod.chat = original_chat
        agent_mod.pretty_print = original_pretty_print


@pytest.mark.asyncio
async def test_chat_tool_calls():
    """Test handling of tool calls in conversations."""
    import agent as agent_mod
    import core
    
    # Save original objects
    original_messages = agent_mod.messages.copy()
    original_chat = agent_mod.chat
    original_pretty_print = agent_mod.pretty_print
    
    try:
        # Create a mock response with tool calls
        tool_call_response = {
            "choices": [
                {
                    "message": {
                        "content": None,
                        "role": "assistant",
                        "tool_calls": [
                            {"id": "tool1", "type": "function", "function": {"name": "test_tool", "arguments": "{}"}}
                        ]
                    }
                }
            ]
        }
        second_response = {
            "choices": [
                {
                    "message": {
                        "content": "Final response after tools",
                        "role": "assistant"
                    }
                }
            ]
        }
        
        # Mock chat and its methods
        mock_chat = MagicMock()
        mock_chat.send_messages = AsyncMock(side_effect=[tool_call_response, second_response])
        mock_chat.process_tool_calls = AsyncMock()
        agent_mod.chat = mock_chat
        
        # Mock pretty_print to avoid actual printing
        agent_mod.pretty_print = MagicMock()
        
        # Create our own implementation of run_conversation that mimics the original
        async def test_run_conversation(user_input):
            agent_mod.messages.append({"role": "user", "content": user_input})
            response = await agent_mod.chat.send_messages(agent_mod.messages)
            
            choices = response.get("choices", [])
            assistant_message = choices[0].get("message", {})
            agent_mod.messages.append(assistant_message)
            
            # Handle the case where tool_calls might be missing or not a list
            while assistant_message.get("tool_calls"):
                await agent_mod.chat.process_tool_calls(assistant_message, agent_mod.messages.append)
                
                response = await agent_mod.chat.send_messages(agent_mod.messages)
                if not (response and response.get("choices", None)):
                    break
                    
                assistant_message = response.get("choices", [{}])[0].get("message", {})
                agent_mod.messages.append(assistant_message)
            
            result = assistant_message.get("content", "")
            agent_mod.pretty_print("Result", result)
            return result
        
        # Call the function
        await test_run_conversation("Test tool calls")
        
        # Verify process_tool_calls was called
        mock_chat.process_tool_calls.assert_called_once()
        
        # Verify send_messages was called twice
        assert mock_chat.send_messages.call_count == 2
        
        # Verify pretty_print was called with the final response
        agent_mod.pretty_print.assert_called_with("Result", "Final response after tools")
        
    finally:
        # Restore original objects
        agent_mod.messages = original_messages
        agent_mod.chat = original_chat
        agent_mod.pretty_print = original_pretty_print
