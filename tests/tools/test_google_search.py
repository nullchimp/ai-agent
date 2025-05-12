"""
Tests for the google_search.py tool
"""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))


class MockSearchResults:
    def __init__(self, query, results, total=1000000):
        self.query = query
        self.results = results
        self.total_results = total
        self.search_time = 0.173074
        self.formatted_count = "483,000,000"


def test_google_search_initialization():
    """Test that GoogleSearch class initializes correctly."""
    from tools.google_search import GoogleSearch
    
    # Initialize with a name
    tool = GoogleSearch("google_search_tool")
    
    # Verify name is set
    assert tool.name == "google_search_tool"
    
    # Verify define method returns schema
    schema = tool.define()
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "google_search_tool"
    assert "description" in schema["function"]
    assert "parameters" in schema["function"]
    assert "query" in schema["function"]["parameters"]["properties"]


@pytest.mark.asyncio
async def test_google_search_run_success():
    """Test the async run method of GoogleSearch."""
    from tools.google_search import GoogleSearch
    
    # Create a mock for the search service
    with patch('libs.search.service.Service.create') as mock_create:
        # Create a mock result object with string results
        mock_results = ["Result 1 (http://example.com/1) - Snippet 1", 
                        "Result 2 (http://example.com/2) - Snippet 2"]
        
        # Create mock search result objects that will be stringified
        class MockResult:
            def __init__(self, data):
                self.data = data
            def __str__(self):
                return self.data
        
        mock_result_objects = [MockResult(r) for r in mock_results]
        
        # Configure the mock service and its response
        mock_search_results = MagicMock()
        mock_search_results.query = "test query"
        mock_search_results.total_results = 1000000
        mock_search_results.search_time = 0.173074
        mock_search_results.formatted_count = "1,000,000"
        mock_search_results.results = mock_result_objects
        
        mock_service = MagicMock()
        mock_service.search.return_value = mock_search_results
        mock_create.return_value = mock_service
        
        # Create an instance of GoogleSearch and run it
        tool = GoogleSearch("google_search")
        result = await tool.run(query="test query")
        
        # Verify the result matches expected structure
        assert result["query"] == "test query"
        assert result["results"] == mock_results
        assert result["total_results"] == 1000000
        assert result["search_time"] == 0.173074
        assert result["formatted_count"] == "1,000,000"
        
        # Verify that the search method was called with the right parameters
        mock_service.search.assert_called_once_with("test query", 5)


@pytest.mark.asyncio
async def test_google_search_run_with_custom_num_results():
    """Test the async run method with custom num_results."""
    from tools.google_search import GoogleSearch
    
    # Create a mock for the search service
    with patch('libs.search.service.Service.create') as mock_create:
        # Create mock result objects that match the actual indices
        class MockResult:
            def __init__(self, i):
                self.i = i
            def __str__(self):
                return f"Result {self.i}"
        
        mock_result_objects = [MockResult(i) for i in range(1, 11)]
        
        # Configure the mock service response
        mock_search_results = MagicMock()
        mock_search_results.query = "test query"
        mock_search_results.results = mock_result_objects
        mock_search_results.total_results = 1000000
        mock_search_results.search_time = 0.25
        mock_search_results.formatted_count = "1,000,000"
        
        mock_service = MagicMock()
        mock_service.search.return_value = mock_search_results
        mock_create.return_value = mock_service
        
        # Create an instance of GoogleSearch and run it with custom num_results
        tool = GoogleSearch("google_search")
        result = await tool.run(query="test query", num_results=10)
        
        # Verify result structure
        assert len(result["results"]) == 10
        
        # Check each result string has the expected format
        for i in range(10):
            assert f"Result {i+1}" in result["results"][i]
        
        # Verify that the search method was called with num_results=10
        mock_service.search.assert_called_once_with("test query", 10)


@pytest.mark.asyncio
async def test_google_search_run_empty_results():
    """Test the async run method with empty results."""
    from tools.google_search import GoogleSearch
    
    # Create a mock for the search service that returns empty results
    with patch('libs.search.service.Service.create') as mock_create:
        # Configure empty search results
        mock_search_results = MagicMock()
        mock_search_results.query = "test query"
        mock_search_results.results = []
        mock_search_results.total_results = 0
        mock_search_results.search_time = 0.1
        mock_search_results.formatted_count = "0"
        
        mock_service = MagicMock()
        mock_service.search.return_value = mock_search_results
        mock_create.return_value = mock_service
        
        # Create an instance of GoogleSearch and run it
        tool = GoogleSearch("google_search")
        result = await tool.run(query="test query")
        
        # Verify empty results are handled correctly
        assert len(result["results"]) == 0
        assert result["query"] == "test query"
        assert result["total_results"] == 0
