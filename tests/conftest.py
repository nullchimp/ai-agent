import os
import sys
import pytest
import asyncio


# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))


# Set standard environment variables for testing
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up the test environment with consistent environment variables."""
    # Store original environment variables to restore later
    original_env = os.environ.copy()
    
    # Set standard test environment variables
    test_env = {
        "AZURE_OPENAI_API_KEY": "dummy-key-for-testing",
        # Add any other environment variables needed for tests
    }
    
    # Apply test environment
    for key, value in test_env.items():
        os.environ[key] = value
    
    # Run the tests
    yield
    
    # Restore original environment
    for key in test_env.keys():
        if key in original_env:
            os.environ[key] = original_env[key]
        else:
            del os.environ[key]


# Configure asyncio for pytest-asyncio
@pytest.fixture(scope="session")
def event_loop_policy():
    """Return the default event loop policy."""
    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture
def event_loop(event_loop_policy):
    """Create an instance of the default event loop for each test case."""
    loop = event_loop_policy.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    asyncio.set_event_loop(None)
    loop.close()


# Add pytest configuration to set the default loop scope
def pytest_configure(config):
    """Configure pytest-asyncio with the default event loop scope."""
    config.addinivalue_line(
        "markers", "asyncio: mark test to run using an asyncio event loop"
    )
    
    # Set the default fixture loop scope
    if hasattr(config, 'asyncio_options'):
        config.asyncio_options.default_fixture_loop_scope = 'function'