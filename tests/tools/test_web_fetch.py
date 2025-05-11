import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

# Import WebFetch class
from tools.web_fetch import WebFetch


@pytest.mark.asyncio
async def test_web_fetch_run_success():
    """Test the WebFetch tool with a successful web request."""
    # Create a mock for the service
    with patch('libs.webfetch.service.WebMarkdownService.create') as mock_create:
        # Configure the mock service
        mock_service = MagicMock()
        mock_service.fetch_as_markdown.return_value = ("Test content\n\n", 200)
        mock_create.return_value = mock_service
        
        # Create an instance of WebFetch and run it
        tool = WebFetch("web_fetch")  # Provide required name parameter
        result = await tool.run(url="http://example.com")
        
        # Verify the result matches actual implementation
        assert result["content"] == "Test content\n\n"
        assert result["status_code"] == 200
        assert result["url"] == "http://example.com"
        
        # Verify that fetch_as_markdown was called with the expected URL
        mock_service.fetch_as_markdown.assert_called_once_with("http://example.com", None)


@pytest.mark.asyncio
async def test_web_fetch_run_with_headers():
    """Test the WebFetch tool with custom headers."""
    # Create a mock for the service
    with patch('libs.webfetch.service.WebMarkdownService.create') as mock_create:
        # Configure the mock service
        mock_service = MagicMock()
        mock_service.fetch_as_markdown.return_value = ("Test with headers\n\n", 200)
        mock_create.return_value = mock_service
        
        # Create an instance of WebFetch and run it with custom headers
        tool = WebFetch("web_fetch")  # Provide required name parameter
        headers = {"User-Agent": "Test Agent", "Accept": "text/html"}
        result = await tool.run(url="http://example.com", headers=headers)
        
        # Verify the result matches actual implementation
        assert result["content"] == "Test with headers\n\n"
        assert result["status_code"] == 200
        
        # Verify that fetch_as_markdown was called with the expected URL and headers
        mock_service.fetch_as_markdown.assert_called_once_with("http://example.com", headers)


@pytest.mark.asyncio
async def test_web_fetch_run_error():
    """Test the WebFetch tool when there's an error fetching the URL."""
    # Create a mock for the service that raises an exception
    with patch('libs.webfetch.service.WebMarkdownService.create') as mock_create:
        # Configure the mock service
        mock_service = MagicMock()
        mock_service.fetch_as_markdown.side_effect = Exception("Connection error")
        mock_create.return_value = mock_service
        
        # Create an instance of WebFetch and run it
        tool = WebFetch("web_fetch")  # Provide required name parameter
        
        try:
            result = await tool.run(url="http://example.com")
            # If no exception was raised, we fail the test
            assert False, "Expected exception was not raised"
        except Exception as e:
            # Verify the exception was correctly propagated
            assert "Connection error" in str(e)


def test_placeholder():
    """This test is just here to ensure pytest doesn't complain when all other tests are skipped."""
    assert True
