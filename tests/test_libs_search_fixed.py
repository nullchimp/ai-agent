import pytest
from unittest.mock import Mock, patch, MagicMock

from src.libs.search.client import GoogleClient, SearchResult, SearchResults


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
        
        expected = "Test Title (https://example.com) - Test snippet"
        assert str(result) == expected


class TestSearchResults:
    
    def test_search_results_creation(self):
        results = [
            SearchResult(
                title="Result 1",
                link="https://example1.com",
                snippet="Snippet 1",
                display_link="example1.com",
                source="Google"
            )
        ]
        
        search_results = SearchResults(
            query="test query",
            total_results=100,
            search_time=0.25,
            results=results,
            formatted_count="About 100 results"
        )
        
        assert search_results.query == "test query"
        assert search_results.total_results == 100
        assert search_results.search_time == 0.25
        assert len(search_results.results) == 1
        assert search_results.formatted_count == "About 100 results"


class TestGoogleClient:
    
    def test_init_success(self):
        with patch('googleapiclient.discovery.build') as mock_build:
            mock_service = Mock()
            mock_build.return_value = mock_service
            
            client = GoogleClient("test_api_key", "test_cx")
            
            assert client.search_cx == "test_cx"
            assert client.source_name == "Google"
            assert client.service == mock_service
            mock_build.assert_called_once_with("customsearch", "v1", developerKey="test_api_key")
    
    def test_init_with_custom_source_name(self):
        with patch('googleapiclient.discovery.build'):
            client = GoogleClient("test_api_key", "test_cx", "Custom Source")
            assert client.source_name == "Custom Source"
    
    def test_init_missing_api_key(self):
        with pytest.raises(ValueError, match="Google API key is required"):
            GoogleClient("", "test_cx")
    
    def test_init_missing_search_cx(self):
        with pytest.raises(ValueError, match="Search engine ID \\(cx\\) is required"):
            GoogleClient("test_api_key", "")
    
    def test_search_success(self):
        mock_response = {
            "searchInformation": {
                "totalResults": "1000",
                "searchTime": 0.123456,
                "formattedTotalResults": "About 1,000 results"
            },
            "items": [
                {
                    "title": "Test Result 1",
                    "link": "https://example1.com",
                    "snippet": "This is a test snippet 1",
                    "displayLink": "example1.com"
                },
                {
                    "title": "Test Result 2",
                    "link": "https://example2.com",
                    "snippet": "This is a test snippet 2",
                    "displayLink": "example2.com"
                }
            ]
        }
        
        with patch('googleapiclient.discovery.build') as mock_build:
            mock_service = Mock()
            mock_cse = Mock()
            mock_list = Mock()
            mock_execute = Mock(return_value=mock_response)
            
            mock_list.execute = mock_execute
            mock_cse.list.return_value = mock_list
            mock_service.cse.return_value = mock_cse
            mock_build.return_value = mock_service
            
            client = GoogleClient("test_api_key", "test_cx")
            results = client.search("test query", 5)
            
            assert isinstance(results, SearchResults)
            assert results.query == "test query"
            assert results.total_results == 1000
            assert results.search_time == 0.123456
            assert results.formatted_count == "About 1,000 results"
            assert len(results.results) == 2
            
            # Check first result
            assert results.results[0].title == "Test Result 1"
            assert results.results[0].link == "https://example1.com"
            assert results.results[0].snippet == "This is a test snippet 1"
            assert results.results[0].display_link == "example1.com"
            assert results.results[0].source == "Google"
            
            # Verify API call
            mock_cse.list.assert_called_once_with(
                q="test query",
                cx="test_cx",
                num=5
            )
    
    def test_search_empty_query(self):
        with patch('googleapiclient.discovery.build'):
            client = GoogleClient("test_api_key", "test_cx")
            
            with pytest.raises(ValueError, match="Search query cannot be empty"):
                client.search("", 5)
    
    def test_search_zero_results_defaults_to_ten(self):
        mock_response = {
            "searchInformation": {
                "totalResults": "0",
                "searchTime": 0.1,
                "formattedTotalResults": "0 results"
            },
            "items": []
        }
        
        with patch('googleapiclient.discovery.build') as mock_build:
            mock_service = Mock()
            mock_cse = Mock()
            mock_list = Mock()
            mock_execute = Mock(return_value=mock_response)
            
            mock_list.execute = mock_execute
            mock_cse.list.return_value = mock_list
            mock_service.cse.return_value = mock_cse
            mock_build.return_value = mock_service
            
            client = GoogleClient("test_api_key", "test_cx")
            client.search("test query", 0)
            
            # Should default to 10 results
            mock_cse.list.assert_called_once_with(
                q="test query",
                cx="test_cx",
                num=10
            )
    
    def test_search_more_than_ten_results_capped_at_ten(self):
        mock_response = {
            "searchInformation": {
                "totalResults": "1000",
                "searchTime": 0.1,
                "formattedTotalResults": "About 1,000 results"
            },
            "items": []
        }
        
        with patch('googleapiclient.discovery.build') as mock_build:
            mock_service = Mock()
            mock_cse = Mock()
            mock_list = Mock()
            mock_execute = Mock(return_value=mock_response)
            
            mock_list.execute = mock_execute
            mock_cse.list.return_value = mock_list
            mock_service.cse.return_value = mock_cse
            mock_build.return_value = mock_service
            
            client = GoogleClient("test_api_key", "test_cx")
            client.search("test query", 50)
            
            # Should be capped at 10 results
            mock_cse.list.assert_called_once_with(
                q="test query",
                cx="test_cx",
                num=10
            )
    
    def test_search_missing_optional_fields(self):
        mock_response = {
            "searchInformation": {},
            "items": [
                {
                    "title": "Test Result",
                    # Missing optional fields
                }
            ]
        }
        
        with patch('googleapiclient.discovery.build') as mock_build:
            mock_service = Mock()
            mock_cse = Mock()
            mock_list = Mock()
            mock_execute = Mock(return_value=mock_response)
            
            mock_list.execute = mock_execute
            mock_cse.list.return_value = mock_list
            mock_service.cse.return_value = mock_cse
            mock_build.return_value = mock_service
            
            client = GoogleClient("test_api_key", "test_cx")
            results = client.search("test query", 5)
            
            # Should handle missing fields gracefully
            assert results.total_results == 0
            assert results.search_time == 0.0
            assert results.formatted_count == "0"
            assert len(results.results) == 1
            assert results.results[0].title == "Test Result"
            assert results.results[0].link == ""
            assert results.results[0].snippet == ""
            assert results.results[0].display_link == ""
    
    def test_search_no_items(self):
        mock_response = {
            "searchInformation": {
                "totalResults": "0",
                "searchTime": 0.05,
                "formattedTotalResults": "0 results"
            }
            # Missing 'items' key
        }
        
        with patch('googleapiclient.discovery.build') as mock_build:
            mock_service = Mock()
            mock_cse = Mock()
            mock_list = Mock()
            mock_execute = Mock(return_value=mock_response)
            
            mock_list.execute = mock_execute
            mock_cse.list.return_value = mock_list
            mock_service.cse.return_value = mock_cse
            mock_build.return_value = mock_service
            
            client = GoogleClient("test_api_key", "test_cx")
            results = client.search("test query", 5)
            
            assert results.total_results == 0
            assert len(results.results) == 0
