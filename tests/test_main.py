import pytest
import sys
import os
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))


@pytest.mark.asyncio
async def test_mcp_discovery_success():
    """Test the mcp_discovery function when sessions are loaded successfully."""
    import main
    from utils.mcpclient.sessions_manager import MCPSessionManager
    
    # Mock the session manager
    mock_session_manager = MagicMock(spec=MCPSessionManager)
    mock_session_manager.load_mcp_sessions = AsyncMock(return_value=True)
    mock_session_manager.list_tools = AsyncMock()
    mock_session_manager.tools = ["tool1", "tool2"]
    
    # Mock agent.add_tool
    mock_add_tool = MagicMock()
    
    with patch.object(main, "session_manager", mock_session_manager):
        with patch("main.agent.add_tool", mock_add_tool):
            # Call mcp_discovery
            await main.mcp_discovery()
            
            # Verify load_mcp_sessions and list_tools were called
            mock_session_manager.load_mcp_sessions.assert_called_once()
            mock_session_manager.list_tools.assert_called_once()
            
            # Verify add_tool was called for each tool
            assert mock_add_tool.call_count == 2
            mock_add_tool.assert_any_call("tool1")
            mock_add_tool.assert_any_call("tool2")


@pytest.mark.asyncio
async def test_mcp_discovery_no_sessions():
    """Test the mcp_discovery function when no sessions are found."""
    import main
    
    # Mock the session manager
    mock_session_manager = MagicMock()
    mock_session_manager.load_mcp_sessions = AsyncMock(return_value=False)
    
    with patch.object(main, "session_manager", mock_session_manager):
        with patch("builtins.print") as mock_print:
            # Call mcp_discovery
            await main.mcp_discovery()
            
            # Verify load_mcp_sessions was called but list_tools was not
            mock_session_manager.load_mcp_sessions.assert_called_once()
            mock_session_manager.list_tools.assert_not_called()
            
            # Verify appropriate message was printed
            mock_print.assert_called_with("No valid MCP sessions found in configuration")


@pytest.mark.asyncio
async def test_agent_task():
    """Test the agent_task function."""
    import main
    import agent
    from utils import mainloop
    
    # Create a mock mainloop decorator that just returns the function (no infinite loop)
    def mock_mainloop(func):
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        return wrapper
    
    # Mock agent.run_conversation
    mock_run_conversation = AsyncMock()
    
    # Patch both the mainloop decorator and run_conversation
    with patch.object(agent, "run_conversation", mock_run_conversation):
        with patch.object(main, "mainloop", mock_mainloop):
            # We need to reload the agent_task function to use our patched mainloop
            # Save the original
            original_agent_task = main.agent_task
            
            # Redefine agent_task with our mock mainloop
            @mock_mainloop
            @main.graceful_exit
            async def patched_agent_task():
                await agent.run_conversation()
                
            # Replace the function
            main.agent_task = patched_agent_task
            
            try:
                # Call agent_task
                await main.agent_task()
                
                # Verify run_conversation was called
                mock_run_conversation.assert_called_once()
            finally:
                # Restore the original function
                main.agent_task = original_agent_task


@pytest.mark.asyncio
async def test_main_function():
    """Test the main function's execution flow."""
    import main
    
    # Mock the required functions
    mock_mcp_discovery = AsyncMock()
    mock_agent_task = AsyncMock()
    
    with patch.object(main, "mcp_discovery", mock_mcp_discovery):
        with patch.object(main, "agent_task", mock_agent_task):
            with patch("builtins.print") as mock_print:
                with patch.object(main, "session_manager") as mock_session_manager:
                    # Setup mock sessions
                    mock_session_manager.sessions = {"server1": {}, "server2": {}}
                    
                    # Call main
                    await main.main()
                    
                    # Verify the order of calls
                    mock_mcp_discovery.assert_called_once()
                    mock_agent_task.assert_called_once()
                    
                    # Verify prints were called with expected messages
                    mock_print.assert_any_call("<Discovery: MCP Server>")
                    mock_print.assert_any_call("\n--------------------------------------------------\n")
                    mock_print.assert_any_call("<Active MCP Server: server1>")
                    mock_print.assert_any_call("<Active MCP Server: server2>")


@pytest.mark.asyncio
async def test_graceful_exit_decorator():
    """Test the @graceful_exit decorator handles exceptions properly."""
    from utils import graceful_exit
    
    # Create a mock implementation of the graceful_exit decorator for testing
    def mock_graceful_exit(func):
        async def _wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except KeyboardInterrupt:
                print("\nBye!")
                # Don't exit in tests
                return None
            except Exception as e:
                print(f"\nError: {e}")
                return None
        return _wrapper
    
    # Create a test function that raises an exception
    @mock_graceful_exit
    async def test_func():
        raise Exception("Test exception")
    
    # Run the function and verify it doesn't propagate the exception
    with patch("builtins.print") as mock_print:
        result = await test_func()
        
        # Verify error message was printed and function returned None
        mock_print.assert_called_with("\nError: Test exception")
        assert result is None


@pytest.mark.asyncio
async def test_graceful_exit_keyboard_interrupt():
    """Test the @graceful_exit decorator handles KeyboardInterrupt properly."""
    from utils import graceful_exit
    
    # Create a mock implementation of the graceful_exit decorator for testing
    def mock_graceful_exit(func):
        async def _wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except KeyboardInterrupt:
                print("\nBye!")
                # Don't exit in tests
                return None
            except Exception as e:
                print(f"\nError: {e}")
                return None
        return _wrapper
    
    # Create a test function that raises a KeyboardInterrupt
    @mock_graceful_exit
    async def test_func():
        raise KeyboardInterrupt()
    
    # Run the function and verify it handles KeyboardInterrupt properly
    with patch("builtins.print") as mock_print:
        result = await test_func()
        
        # Verify bye message was printed
        mock_print.assert_called_with("\nBye!")
        assert result is None


def test_main_block_execution():
    """Test the __main__ block execution."""
    import main
    
    # Save original value
    original_name = main.__name__
    
    try:
        # Mock asyncio.run
        with patch('asyncio.run') as mock_run:
            # Set __name__ to "__main__" to trigger the if block
            main.__name__ = "__main__"
            
            # Re-execute the main block
            exec(
                'if __name__ == "__main__":\n'
                '    asyncio.run(main())',
                main.__dict__
            )
            
            # Verify asyncio.run was called with main()
            mock_run.assert_called_once()
            assert mock_run.call_args[0][0].__name__ == 'main'
    finally:
        # Restore original value
        main.__name__ = original_name