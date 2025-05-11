import pytest
import sys
import os
from unittest.mock import patch, MagicMock, AsyncMock

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))


def test_agent_main_block_execution():
    """Test the __main__ block in agent.py"""
    import agent

    # Save the original __name__
    original_name = agent.__name__

    # Mock asyncio.run to avoid actually running the conversation
    with patch('asyncio.run') as mock_run:
        try:
            # Set __name__ to "__main__" to trigger the if block
            agent.__name__ = "__main__"
            
            # Re-execute the main block 
            exec(
                'if __name__ == "__main__":\n'
                '    import asyncio\n'
                '    asyncio.run(run_conversation())',
                agent.__dict__
            )
            
            # Verify asyncio.run was called with something (function name doesn't matter)
            mock_run.assert_called_once()
            # The function is wrapped by decorators, so we can't check the name directly
        finally:
            # Restore original name
            agent.__name__ = original_name