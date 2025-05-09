import pytest
from tools.web_fetch import WebFetch
from unittest.mock import patch, MagicMock


def test_web_fetch_run_success():
    tool = WebFetch()
    with patch("libs.webfetch.service.WebMarkdownService") as MockService:
        instance = MockService.create.return_value
        instance.fetch_as_markdown.return_value = ("# markdown", 200)
        out = tool.run("http://example.com")
        assert out["url"] == "http://example.com"
        assert out["status_code"] == 200
        assert out["markdown_content"] == "# markdown"


def test_web_fetch_run_with_headers():
    tool = WebFetch()
    with patch("libs.webfetch.service.WebMarkdownService") as MockService:
        instance = MockService.create.return_value
        instance.fetch_as_markdown.return_value = ("# md", 201)
        headers = {"X-Test": "1"}
        out = tool.run("http://example.com", headers=headers)
        instance.fetch_as_markdown.assert_called_with("http://example.com", headers)
        assert out["status_code"] == 201
        assert out["markdown_content"] == "# md"


def test_web_fetch_run_error():
    tool = WebFetch()
    with patch("libs.webfetch.service.WebMarkdownService") as MockService:
        instance = MockService.create.return_value
        instance.fetch_as_markdown.side_effect = Exception("fail")
        with pytest.raises(Exception):
            tool.run("http://fail.com")


def test_placeholder():
    assert True
