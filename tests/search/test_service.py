"""
Tests for search service module.
"""
import os
from unittest import mock
import pytest

from src.search.service import Service
from src.search.client import SearchResults, SearchResult


@pytest.fixture
def mock_search_client():
    """Create a mock search client."""
    client = mock.MagicMock()
    
    # Configure the mock search method to return test results
    client.search.return_value = SearchResults(
        query="test query",
        total_results=100,
        search_time=0.3,
        formatted_count="100",
        results=[
            SearchResult(
                title="Test Result",
                link="https://example.com",
                snippet="Test snippet",
                display_link="example.com",
                source="Test Source"
            )
        ]
    )
    
    return client


def test_service_init():
    """Test Service initialization with client."""
    mock_client = mock.MagicMock()
    service = Service(client=mock_client)
    
    assert service.client == mock_client


def test_service_create():
    """Test Service.create factory method with environment variables."""
    # Mock environment variables
    env_vars = {
        "GOOGLE_API_KEY": "test-key",
        "GOOGLE_SEARCH_ENGINE_ID": "test-cx"
    }
    
    with mock.patch.dict(os.environ, env_vars):
        with mock.patch("src.search.service.GoogleClient") as mock_client_cls:
            # Create the service
            service = Service.create()
            
            # Verify GoogleClient was created with correct parameters
            mock_client_cls.assert_called_once_with(
                api_key="test-key",
                search_cx="test-cx"
            )
            
            assert service.client == mock_client_cls.return_value


def test_service_create_missing_env_vars():
    """Test Service.create fails with missing environment variables."""
    # Ensure environment variables are cleared
    with mock.patch.dict(os.environ, clear=True):
        with pytest.raises(ValueError) as exc_info:
            Service.create()
        
        assert "Missing required environment variables" in str(exc_info.value)


def test_service_search(mock_search_client):
    """Test the search method delegates to the client correctly."""
    service = Service(client=mock_search_client)
    
    # Call the search method
    results = service.search("test query", 5)
    
    # Verify the client's search method was called with correct parameters
    mock_search_client.search.assert_called_once_with("test query", 5)
    
    # Verify the results were returned correctly
    assert results == mock_search_client.search.return_value
    assert results.query == "test query"
    assert len(results.results) == 1
    assert results.results[0].title == "Test Result"


def test_service_search_with_default_num_results(mock_search_client):
    """Test search with default number of results."""
    service = Service(client=mock_search_client)
    
    # Call search without specifying num_results
    service.search("test query")
    
    # Verify client search was called with default value
    mock_search_client.search.assert_called_once_with("test query", 10)


def test_service_search_with_no_client():
    """Test search with no client raises ValueError."""
    # Create service with no client
    service = Service(client=None)
    
    with pytest.raises(ValueError) as exc_info:
        service.search("test query")
    
    assert "Search client not configured" in str(exc_info.value)