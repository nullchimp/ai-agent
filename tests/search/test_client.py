"""
Tests for Google search client module.
"""
from unittest import mock
import pytest

from src.search.client import GoogleClient, SearchResult, SearchResults


@pytest.fixture
def mock_google_service():
    """Create a mock Google API service."""
    mock_service = mock.MagicMock()
    
    # Set up the response structure
    mock_cse_resource = mock.MagicMock()
    mock_service.cse.return_value = mock_cse_resource
    mock_list_method = mock.MagicMock()
    mock_cse_resource.list.return_value = mock_list_method
    
    # Set up the mock response
    mock_response = {
        "items": [
            {
                "title": "Test Result 1",
                "link": "https://example.com/1",
                "snippet": "This is test result 1",
                "displayLink": "example.com"
            },
            {
                "title": "Test Result 2",
                "link": "https://example.com/2", 
                "snippet": "This is test result 2",
                "displayLink": "example.com"
            }
        ],
        "searchInformation": {
            "totalResults": "1234567",
            "searchTime": 0.5,
            "formattedTotalResults": "1,234,567"
        }
    }
    
    mock_list_method.execute.return_value = mock_response
    
    # Set up method chaining for query parameters
    mock_list_method.q.return_value = mock_list_method
    mock_list_method.cx.return_value = mock_list_method
    mock_list_method.num.return_value = mock_list_method
    
    return mock_service


def test_google_client_init_missing_api_key():
    """Test that GoogleClient initialization fails with missing API key."""
    with pytest.raises(ValueError) as exc_info:
        GoogleClient(api_key="", search_cx="test-cx")
    
    assert "Google API key is required" in str(exc_info.value)


def test_google_client_init_missing_search_cx():
    """Test that GoogleClient initialization fails with missing search engine ID."""
    with pytest.raises(ValueError) as exc_info:
        GoogleClient(api_key="test-key", search_cx="")
    
    assert "Search engine ID (cx) is required" in str(exc_info.value)


@mock.patch('googleapiclient.discovery.build')
def test_google_client_init_success(mock_build):
    """Test successful initialization of GoogleClient."""
    mock_service = mock.MagicMock()
    mock_build.return_value = mock_service
    
    client = GoogleClient(
        api_key="test-key", 
        search_cx="test-cx",
        source_name="Test Source"
    )
    
    # Verify the service was built correctly
    mock_build.assert_called_once_with(
        "customsearch", "v1", 
        developerKey="test-key"
    )
    
    # Verify client properties
    assert client.service == mock_service
    assert client.search_cx == "test-cx"
    assert client.source_name == "Test Source"


def test_search_with_empty_query(mock_google_service):
    """Test search with empty query raises ValueError."""
    client = GoogleClient(api_key="test-key", search_cx="test-cx")
    client.service = mock_google_service
    
    with pytest.raises(ValueError) as exc_info:
        client.search("", 10)
    
    assert "Search query cannot be empty" in str(exc_info.value)


def test_search_with_default_num_results(mock_google_service):
    """Test search with negative or zero num_results uses default."""
    client = GoogleClient(api_key="test-key", search_cx="test-cx")
    client.service = mock_google_service
    
    # Test with negative number
    client.search("test query", -5)
    
    # Verify 10 (default) was used
    mock_google_service.cse().list().num.assert_called_with(10)


def test_search_with_large_num_results(mock_google_service):
    """Test search with num_results > 10 is limited to 10."""
    client = GoogleClient(api_key="test-key", search_cx="test-cx")
    client.service = mock_google_service
    
    # Test with number > 10
    client.search("test query", 20)
    
    # Verify 10 (maximum) was used
    mock_google_service.cse().list().num.assert_called_with(10)


def test_search_success(mock_google_service):
    """Test successful search and result parsing."""
    client = GoogleClient(api_key="test-key", search_cx="test-cx")
    client.service = mock_google_service
    
    results = client.search("test query", 2)
    
    # Verify query parameters were set correctly
    mock_google_service.cse().list.assert_called_once()
    mock_google_service.cse().list().q.assert_called_with("test query")
    mock_google_service.cse().list().cx.assert_called_with("test-cx")
    mock_google_service.cse().list().num.assert_called_with(2)
    mock_google_service.cse().list().execute.assert_called_once()
    
    # Check result object structure
    assert isinstance(results, SearchResults)
    assert results.query == "test query"
    assert results.total_results == 1234567
    assert results.search_time == 0.5
    assert results.formatted_count == "1,234,567"
    
    # Check individual results
    assert len(results.results) == 2
    
    assert results.results[0].title == "Test Result 1"
    assert results.results[0].link == "https://example.com/1"
    assert results.results[0].snippet == "This is test result 1"
    assert results.results[0].display_link == "example.com"
    
    assert results.results[1].title == "Test Result 2"
    assert results.results[1].link == "https://example.com/2"
    assert results.results[1].snippet == "This is test result 2"
    assert results.results[1].display_link == "example.com"