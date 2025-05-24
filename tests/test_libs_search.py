import pytest
from unittest.mock import Mock, patch, MagicMock
import os
from dataclasses import dataclass

from libs.search.client import SearchResult, SearchResults, GoogleClient
from libs.search.service import Service


class TestSearchResult:

    def test_search_result_creation(self):
        result = SearchResult(
            title="Test Title",
            link="https://example.com",
            snippet="Test snippet",
            display_link="example.com",
            source="Google"
        )
        
        assert result.title == "Test Title"
        assert result.link == "https://example.com"
        assert result.snippet == "Test snippet"
        assert result.display_link == "example.com"
        assert result.source == "Google"

    def test_search_result_str(self):
        result = SearchResult(
            title="Test Title",
            link="https://example.com",
            snippet="Test snippet",
            display_link="example.com",
            source="Google"
        )
        
        str_result = str(result)
        assert "Test Title" in str_result
        assert "https://example.com" in str_result
        assert "Test snippet" in str_result


class TestSearchResults:

    def test_search_results_creation(self):
        results = [
            SearchResult("Title1", "https://example1.com", "Snippet1", "example1.com", "Google"),
            SearchResult("Title2", "https://example2.com", "Snippet2", "example2.com", "Google")
        ]
        
        search_results = SearchResults(
            query="test query",
            total_results=2,
            search_time=0.123,
            results=results,
            formatted_count="2"
        )
        
        assert search_results.query == "test query"
        assert search_results.total_results == 2
        assert search_results.search_time == 0.123
        assert len(search_results.results) == 2
        assert search_results.formatted_count == "2"


class TestGoogleClient:

    def test_google_client_init_success(self):
        client = GoogleClient("test_api_key", "test_cx")
        assert client.search_cx == "test_cx"
        assert client.source_name == "Google"

    def test_google_client_init_missing_api_key(self):
        with pytest.raises(ValueError, match="Google API key is required"):
            GoogleClient("", "test_cx")

    def test_google_client_init_missing_cx(self):
        with pytest.raises(ValueError, match="Search engine ID .* is required"):
            GoogleClient("test_api_key", "")

    def test_google_client_init_custom_source(self):
        client = GoogleClient("test_api_key", "test_cx", "Custom Source")
        assert client.source_name == "Custom Source"

    @patch('googleapiclient.discovery.build')
    def test_google_client_search_success(self, mock_build):
        # Mock the Google API service
        mock_service = Mock()
        mock_cse = Mock()
        mock_list = Mock()
        
        mock_response = {
            "searchInformation": {
                "totalResults": "100",
                "searchTime": 0.456,
                "formattedTotalResults": "100"
            },
            "items": [
                {
                    "title": "Test Result 1",
                    "link": "https://example1.com",
                    "snippet": "Test snippet 1",
                    "displayLink": "example1.com"
                },
                {
                    "title": "Test Result 2",
                    "link": "https://example2.com",
                    "snippet": "Test snippet 2",
                    "displayLink": "example2.com"
                }
            ]
        }
        
        mock_list.execute.return_value = mock_response
        mock_cse.list.return_value = mock_list
        mock_service.cse.return_value = mock_cse
        mock_build.return_value = mock_service
        
        client = GoogleClient("test_api_key", "test_cx")
        results = client.search("test query", 5)
        
        assert results.query == "test query"
        assert results.total_results == 100
        assert results.search_time == 0.456
        assert results.formatted_count == "100"
        assert len(results.results) == 2
        
        # Check first result
        first_result = results.results[0]
        assert first_result.title == "Test Result 1"
        assert first_result.link == "https://example1.com"
        assert first_result.snippet == "Test snippet 1"
        assert first_result.display_link == "example1.com"
        assert first_result.source == "Google"

    @patch('googleapiclient.discovery.build')
    def test_google_client_search_empty_query(self, mock_build):
        client = GoogleClient("test_api_key", "test_cx")
        
        with pytest.raises(ValueError, match="Search query cannot be empty"):
            client.search("", 5)

    @patch('googleapiclient.discovery.build')
    def test_google_client_search_invalid_num_results(self, mock_build):
        mock_service = Mock()
        mock_cse = Mock()
        mock_list = Mock()
        
        mock_response = {
            "searchInformation": {
                "totalResults": "0",
                "searchTime": 0.0,
                "formattedTotalResults": "0"
            },
            "items": []
        }
        
        mock_list.execute.return_value = mock_response
        mock_cse.list.return_value = mock_list
        mock_service.cse.return_value = mock_cse
        mock_build.return_value = mock_service
        
        client = GoogleClient("test_api_key", "test_cx")
        
        # Test zero results
        results = client.search("test", 0)
        mock_cse.list.assert_called_with(q="test", cx="test_cx", num=10)
        
        # Test over limit
        results = client.search("test", 15)
        mock_cse.list.assert_called_with(q="test", cx="test_cx", num=10)

    @patch('googleapiclient.discovery.build')
    def test_google_client_search_no_items(self, mock_build):
        mock_service = Mock()
        mock_cse = Mock()
        mock_list = Mock()
        
        mock_response = {
            "searchInformation": {
                "totalResults": "0",
                "searchTime": 0.0,
                "formattedTotalResults": "0"
            }
            # No "items" key
        }
        
        mock_list.execute.return_value = mock_response
        mock_cse.list.return_value = mock_list
        mock_service.cse.return_value = mock_cse
        mock_build.return_value = mock_service
        
        client = GoogleClient("test_api_key", "test_cx")
        results = client.search("test query", 5)
        
        assert len(results.results) == 0

    @patch('googleapiclient.discovery.build')
    def test_google_client_search_missing_fields(self, mock_build):
        mock_service = Mock()
        mock_cse = Mock()
        mock_list = Mock()
        
        mock_response = {
            "searchInformation": {},
            "items": [
                {
                    # Missing some fields
                    "title": "Test Result",
                    "link": "https://example.com"
                    # Missing snippet, displayLink
                }
            ]
        }
        
        mock_list.execute.return_value = mock_response
        mock_cse.list.return_value = mock_list
        mock_service.cse.return_value = mock_cse
        mock_build.return_value = mock_service
        
        client = GoogleClient("test_api_key", "test_cx")
        results = client.search("test query", 5)
        
        assert results.total_results == 0  # Default when missing
        assert results.search_time == 0.0  # Default when missing
        assert len(results.results) == 1
        
        result = results.results[0]
        assert result.title == "Test Result"
        assert result.link == "https://example.com"
        assert result.snippet == ""  # Default empty string
        assert result.display_link == ""  # Default empty string


class TestService:

    @patch.dict(os.environ, {
        "GOOGLE_API_KEY": "test_api_key",
        "GOOGLE_SEARCH_ENGINE_ID": "test_engine_id"
    })
    @patch('libs.search.service.GoogleClient')
    def test_service_create_success(self, mock_google_client):
        mock_client_instance = Mock()
        mock_google_client.return_value = mock_client_instance
        
        service = Service.create()
        
        assert service.client == mock_client_instance
        mock_google_client.assert_called_once_with(
            api_key="test_api_key",
            search_cx="test_engine_id"
        )

    @patch.dict(os.environ, {}, clear=True)
    def test_service_create_missing_env_vars(self):
        with pytest.raises(ValueError, match="Missing required environment variables"):
            Service.create()

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"})
    def test_service_create_missing_engine_id(self):
        # This should not raise an error because GOOGLE_ENGINE_ID has a default
        service = Service.create()
        assert service is not None

    def test_service_init(self):
        mock_client = Mock()
        service = Service(mock_client)
        assert service.client == mock_client

    def test_service_search_success(self):
        mock_client = Mock()
        mock_results = SearchResults(
            query="test",
            total_results=1,
            search_time=0.1,
            results=[],
            formatted_count="1"
        )
        mock_client.search.return_value = mock_results
        
        service = Service(mock_client)
        results = service.search("test query", 5)
        
        assert results == mock_results
        mock_client.search.assert_called_once_with("test query", 5)

    def test_service_search_no_client(self):
        service = Service(None)
        
        with pytest.raises(ValueError, match="Search client not configured"):
            service.search("test query", 5)
