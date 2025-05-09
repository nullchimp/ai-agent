import pytest
from unittest.mock import patch, MagicMock
from libs.search.client import GoogleClient, SearchResult, SearchResults


@pytest.fixture
def google_client():
    return GoogleClient(api_key="dummy", search_cx="dummy_cx")


def test_search_success(monkeypatch, google_client):
    mock_service = MagicMock()
    mock_cse = MagicMock()
    mock_list = MagicMock()
    mock_list.execute.return_value = {
        "searchInformation": {
            "totalResults": "2",
            "searchTime": 0.1,
            "formattedTotalResults": "2",
        },
        "items": [
            {"title": "A", "link": "urlA", "snippet": "descA", "displayLink": "dispA"},
            {"title": "B", "link": "urlB", "snippet": "descB", "displayLink": "dispB"},
        ],
    }
    mock_cse.list.return_value = mock_list
    mock_service.cse.return_value = mock_cse
    monkeypatch.setattr(google_client, "service", mock_service)
    results = google_client.search("test", 2)
    assert isinstance(results, SearchResults)
    assert results.total_results == 2
    assert len(results.results) == 2
    assert results.results[0].title == "A"


def test_search_empty_query(google_client):
    with pytest.raises(ValueError):
        google_client.search("", 1)


def test_search_invalid_num_results(google_client, monkeypatch):
    # Should default to 10 if num_results <= 0
    mock_service = MagicMock()
    mock_cse = MagicMock()
    mock_list = MagicMock()
    mock_list.execute.return_value = {"searchInformation": {}, "items": []}
    mock_cse.list.return_value = mock_list
    mock_service.cse.return_value = mock_cse
    monkeypatch.setattr(google_client, "service", mock_service)
    google_client.search("test", -1)
    google_client.search("test", 100)
