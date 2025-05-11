import pytest
import sys
import os
from unittest.mock import patch, MagicMock, AsyncMock

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

# Import tool classes
from tools.google_search import GoogleSearch


class MockSearchResults:
    def __init__(self, query, results, total=1000000):
        self.query = query
        self.results = results
        self.total_results = total
        self.search_time = 0.173074
        self.formatted_count = "483,000,000"


@pytest.mark.asyncio
async def test_google_search_run_success():
    # Create a mock for the search service
    with patch('libs.search.service.Service.create') as mock_create:
        # Configure mock results
        mock_results = [
            "Result 1 (http://example.com/1) - Snippet 1",
            "Result 2 (http://example.com/2) - Snippet 2"
        ]
        mock_search_results = MockSearchResults("test query", mock_results)
        
        # Configure the mock service
        mock_service = MagicMock()
        mock_service.search.return_value = mock_search_results
        mock_create.return_value = mock_service
        
        # Create an instance of GoogleSearch and run it
        tool = GoogleSearch("google_search")  # Provide required name parameter
        result = await tool.run(query="test query")
        
        # Verify the result matches actual implementation
        assert result["query"] == "test query"
        assert result["results"] == mock_results
        assert "total_results" in result
        assert "search_time" in result
        assert "formatted_count" in result
        
        # Verify that the search method was called with the right parameters
        mock_service.search.assert_called_once_with("test query", 5)


@pytest.mark.asyncio
async def test_google_search_run_with_custom_num_results():
    # Create a mock for the search service
    with patch('libs.search.service.Service.create') as mock_create:
        # Configure mock results
        mock_results = [f"Result {i}" for i in range(1, 11)]
        mock_search_results = MockSearchResults("test query", mock_results)
        
        # Configure the mock service
        mock_service = MagicMock()
        mock_service.search.return_value = mock_search_results
        mock_create.return_value = mock_service
        
        # Create an instance of GoogleSearch and run it with custom num_results
        tool = GoogleSearch("google_search")
        result = await tool.run(query="test query", num_results=10)
        
        # Verify result structure
        assert len(result["results"]) == 10
        
        # Verify that the search method was called with num_results=10
        mock_service.search.assert_called_once_with("test query", 10)


@pytest.mark.asyncio
async def test_google_search_run_empty_results():
    # Create a mock for the search service that returns empty results
    with patch('libs.search.service.Service.create') as mock_create:
        # Configure empty search results
        mock_search_results = MockSearchResults("test query", [])
        
        # Configure the mock service
        mock_service = MagicMock()
        mock_service.search.return_value = mock_search_results
        mock_create.return_value = mock_service
        
        # Create an instance of GoogleSearch and run it
        tool = GoogleSearch("google_search")
        result = await tool.run(query="test query")
        
        # Verify empty results are handled correctly
        assert len(result["results"]) == 0
        assert result["query"] == "test query"
