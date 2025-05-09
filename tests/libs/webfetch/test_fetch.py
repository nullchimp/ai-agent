import pytest
from unittest.mock import patch, MagicMock
from libs.webfetch.fetch import WebFetcher


@patch("libs.webfetch.fetch.requests.get")
def test_fetch_content_success(mock_get):
    mock_response = MagicMock()
    mock_response.text = "<html>hi</html>"
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response
    fetcher = WebFetcher.create()
    content, status = fetcher.fetch_content("http://example.com")
    assert content == "<html>hi</html>"
    assert status == 200


@patch("libs.webfetch.fetch.requests.get")
def test_fetch_content_error(mock_get):
    mock_get.side_effect = Exception("fail")
    fetcher = WebFetcher.create()
    with pytest.raises(Exception):
        fetcher.fetch_content("http://bad.com")


def test_fetch_content_with_headers():
    # Test that custom headers are merged and passed to requests.get
    with patch("libs.webfetch.fetch.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = "<html>header</html>"
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        fetcher = WebFetcher.create()
        custom_headers = {"X-Test": "1"}
        content, status = fetcher.fetch_content("http://example.com", headers=custom_headers)
        assert content == "<html>header</html>"
        assert status == 200
        # Ensure headers are merged
        args, kwargs = mock_get.call_args
        assert "X-Test" in kwargs["headers"]
        assert kwargs["headers"]["X-Test"] == "1"


def test_fetch_content_request_exception():
    # Test that requests.RequestException is raised as-is
    import requests
    with patch("libs.webfetch.fetch.requests.get") as mock_get:
        mock_get.side_effect = requests.RequestException("network error")
        fetcher = WebFetcher.create()
        with pytest.raises(requests.RequestException):
            fetcher.fetch_content("http://fail.com")


def test_placeholder():
    assert True
