import pytest
from unittest.mock import MagicMock, patch
from libs.webfetch.service import WebMarkdownService


def test_fetch_as_markdown_success():
    mock_fetcher = MagicMock()
    mock_converter = MagicMock()
    mock_fetcher.fetch_content.return_value = ("<html>hi</html>", 200)
    mock_converter.convert.return_value = "# hi"
    service = WebMarkdownService(mock_fetcher, mock_converter)
    md, status = service.fetch_as_markdown("http://example.com")
    assert md == "# hi"
    assert status == 200


def test_create_factory():
    service = WebMarkdownService.create()
    assert isinstance(service, WebMarkdownService)


@patch("libs.webfetch.service.WebFetcher")
@patch("libs.webfetch.service.HtmlToMarkdownConverter")
def test_create_factory_mocks(mock_converter, mock_fetcher):
    mock_fetcher.create.return_value = MagicMock()
    mock_converter.create.return_value = MagicMock()
    service = WebMarkdownService.create()
    assert isinstance(service, WebMarkdownService)


def test_fetch_as_markdown_with_html():
    mock_fetcher = MagicMock()
    mock_converter = MagicMock()
    mock_fetcher.fetch_content.return_value = ("<html>test</html>", 200)
    mock_converter.convert.return_value = "# test"
    service = WebMarkdownService(mock_fetcher, mock_converter)
    md, status = service.fetch_as_markdown("http://example.com")
    assert md == "# test"
    assert status == 200


def test_fetch_as_markdown_with_headers():
    mock_fetcher = MagicMock()
    mock_converter = MagicMock()
    mock_fetcher.fetch_content.return_value = ("<html>header</html>", 201)
    mock_converter.convert.return_value = "# header"
    service = WebMarkdownService(mock_fetcher, mock_converter)
    headers = {"X-Test": "1"}
    md, status = service.fetch_as_markdown("http://example.com", headers)
    mock_fetcher.fetch_content.assert_called_with("http://example.com", headers)
    assert md == "# header"
    assert status == 201


def test_fetch_as_markdown_converter_error():
    mock_fetcher = MagicMock()
    mock_converter = MagicMock()
    mock_fetcher.fetch_content.return_value = ("<html>fail</html>", 200)
    mock_converter.convert.side_effect = Exception("convert error")
    service = WebMarkdownService(mock_fetcher, mock_converter)
    with pytest.raises(Exception):
        service.fetch_as_markdown("http://fail.com")


def test_create_factory_types():
    service = WebMarkdownService.create()
    assert isinstance(service, WebMarkdownService)
    assert hasattr(service, "fetcher")
    assert hasattr(service, "converter")
