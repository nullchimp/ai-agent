"""
Tests for the web_fetch.py tool
"""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock
from typing import Dict, Optional

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))


def test_web_fetch_initialization():
    """Test that WebFetch class initializes correctly."""
    from tools.web_fetch import WebFetch
    
    # Initialize with a name
    tool = WebFetch("web_fetch_tool")
    
    # Verify name is set
    assert tool.name == "web_fetch_tool"
    
    # Verify schema structure via define() method
    schema = tool.define()
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "web_fetch_tool"
    assert "description" in schema["function"]
    assert "parameters" in schema["function"]
    
    # Check required parameters
    params = schema["function"]["parameters"]
    assert "url" in params["properties"]
    assert "headers" in params["properties"]
    assert "url" in params["required"]
    assert "headers" not in params["required"]  # headers is optional


@pytest.mark.asyncio
async def test_web_fetch_success():
    """Test successful execution of WebFetch."""
    from tools.web_fetch import WebFetch
    
    # Create a mock for WebMarkdownService
    with patch('libs.webfetch.service.WebMarkdownService') as MockService:
        # Configure the mock
        mock_service_instance = MagicMock()
        mock_service_instance.fetch_as_markdown.return_value = ("# Markdown Content", 200)
        MockService.create.return_value = mock_service_instance
        
        # Create tool and execute
        tool = WebFetch("web_fetch")
        result = await tool.run(url="https://example.com")
        
        # Verify service was created
        MockService.create.assert_called_once()
        
        # Verify fetch_as_markdown was called with correct URL and no headers
        mock_service_instance.fetch_as_markdown.assert_called_once_with("https://example.com", None)
        
        # Verify result structure
        assert result["url"] == "https://example.com"
        assert result["status_code"] == 200
        assert result["content"] == "# Markdown Content"


@pytest.mark.asyncio
async def test_web_fetch_with_headers():
    """Test execution of WebFetch with custom headers."""
    from tools.web_fetch import WebFetch
    
    # Create a mock for WebMarkdownService
    with patch('libs.webfetch.service.WebMarkdownService') as MockService:
        # Configure the mock
        mock_service_instance = MagicMock()
        mock_service_instance.fetch_as_markdown.return_value = ("# Content with Headers", 200)
        MockService.create.return_value = mock_service_instance
        
        # Custom headers
        headers = {"User-Agent": "Test Agent", "Accept-Language": "en-US"}
        
        # Create tool and execute with headers
        tool = WebFetch("web_fetch")
        result = await tool.run(url="https://example.com", headers=headers)
        
        # Verify fetch_as_markdown was called with correct URL and headers
        mock_service_instance.fetch_as_markdown.assert_called_once_with("https://example.com", headers)
        
        # Verify result structure
        assert result["url"] == "https://example.com"
        assert result["status_code"] == 200
        assert result["content"] == "# Content with Headers"


@pytest.mark.asyncio
async def test_web_fetch_error_response():
    """Test WebFetch with an error response."""
    from tools.web_fetch import WebFetch
    
    # Create a mock for WebMarkdownService
    with patch('libs.webfetch.service.WebMarkdownService') as MockService:
        # Configure the mock to return an error status code
        mock_service_instance = MagicMock()
        mock_service_instance.fetch_as_markdown.return_value = ("Error fetching page: Not Found", 404)
        MockService.create.return_value = mock_service_instance
        
        # Create tool and execute
        tool = WebFetch("web_fetch")
        result = await tool.run(url="https://example.com/nonexistent")
        
        # Verify fetch_as_markdown was called
        mock_service_instance.fetch_as_markdown.assert_called_once_with("https://example.com/nonexistent", None)
        
        # Verify result structure for error case
        assert result["url"] == "https://example.com/nonexistent"
        assert result["status_code"] == 404
        assert "Error fetching page" in result["content"]


@pytest.mark.asyncio
async def test_web_fetch_service_exception_handling():
    """Test WebFetch exception handling."""
    from tools.web_fetch import WebFetch
    
    # Create a mock for WebMarkdownService
    with patch('libs.webfetch.service.WebMarkdownService') as MockService:
        # Configure the mock to raise an exception
        mock_service_instance = MagicMock()
        mock_service_instance.fetch_as_markdown.side_effect = Exception("Connection error")
        MockService.create.return_value = mock_service_instance
        
        # Create tool and execute
        tool = WebFetch("web_fetch")
        
        # The current implementation doesn't handle exceptions, so test should expect an exception
        with pytest.raises(Exception, match="Connection error"):
            await tool.run(url="https://example.com")
