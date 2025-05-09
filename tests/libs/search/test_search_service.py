import pytest
from unittest.mock import patch, MagicMock
from libs.search.service import Service


@patch("libs.search.service.GoogleClient")
def test_service_create_success(mock_google_client):
    with patch.dict("os.environ", {"GOOGLE_API_KEY": "key", "GOOGLE_SEARCH_ENGINE_ID": "cx"}):
        service = Service.create()
        assert isinstance(service, Service)
        assert hasattr(service, "client")


@patch("libs.search.service.GoogleClient")
def test_service_create_missing_env(mock_google_client):
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError):
            Service.create()


def test_service_search_success():
    mock_client = MagicMock()
    mock_client.search.return_value = "results"
    service = Service(mock_client)
    result = service.search("query", 5)
    assert result == "results"


def test_service_search_no_client():
    service = Service(None)
    with pytest.raises(ValueError):
        service.search("query", 5)


def test_placeholder():
    assert True
