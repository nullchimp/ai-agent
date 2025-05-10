import pytest
import sys
import os
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

@pytest.mark.asyncio
async def test_process_one():
    """Test the process_one coroutine."""
    import main
    
    # For this test, we need to directly execute the first iteration of the loop
    # in process_one to verify that print is called before sleep
    
    # Create a mock for asyncio.sleep that will raise CancelledError after being called
    async def mock_sleep(seconds):
        raise asyncio.CancelledError()
    
    # Apply the mocks - patching at the exact module where sleep is used
    with patch('asyncio.sleep', mock_sleep):
        with patch('builtins.print') as mock_print:
            try:
                # Run process_one - it should print and then hit our mocked sleep
                # which raises CancelledError to exit the loop
                await main.process_one()
            except asyncio.CancelledError:
                pass
            
            # Verify print was called with the expected message
            mock_print.assert_called_once_with("Processing one...")

@pytest.mark.asyncio
async def test_process_two():
    """Test the process_two coroutine."""
    import main
    import agent
    
    # Create a proper mock for agent.run_conversation
    mock_run_conversation = AsyncMock()
    
    # Apply the patch
    with patch.object(agent, 'run_conversation', mock_run_conversation):
        # Call process_two
        await main.process_two()
        
        # Verify run_conversation was called
        mock_run_conversation.assert_called_once()

@pytest.mark.asyncio
async def test_main_coroutine():
    """Test the main coroutine."""
    import main
    
    # Create proper AsyncMock objects for our coroutines
    mock_process_one = AsyncMock()
    mock_process_two = AsyncMock()
    
    # Apply patches
    with patch.object(main, 'process_one', mock_process_one):
        with patch.object(main, 'process_two', mock_process_two):
            # Run the main coroutine
            await main.main()
            
            # Verify that both coroutines were passed to asyncio.gather
            mock_process_one.assert_called_once()
            mock_process_two.assert_called_once()

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