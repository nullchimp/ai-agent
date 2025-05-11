import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from tools.web_fetch import WebFetch


@pytest.mark.asyncio
async def test_web_fetch_run_success():
    tool = WebFetch()
    with patch("libs.webfetch.service.WebMarkdownService") as MockService:
        instance = MockService.create.return_value
        instance.fetch_as_markdown.return_value = ("# markdown", 200)
        out = await tool.run("http://example.com")
        assert out["url"] == "http://example.com"
        assert out["markdown_content"] == "# markdown"
        assert out["status_code"] == 200
        instance.fetch_as_markdown.assert_called_once_with("http://example.com", None)


@pytest.mark.asyncio
async def test_web_fetch_run_with_headers():
    tool = WebFetch()
    with patch("libs.webfetch.service.WebMarkdownService") as MockService:
        instance = MockService.create.return_value
        instance.fetch_as_markdown.return_value = ("# md", 201)
        headers = {"X-Test": "1"}
        out = await tool.run("http://example.com", headers=headers)
        assert out["url"] == "http://example.com"
        assert out["markdown_content"] == "# md"
        assert out["status_code"] == 201
        instance.fetch_as_markdown.assert_called_with("http://example.com", headers)


@pytest.mark.asyncio
async def test_web_fetch_run_error():
    tool = WebFetch()
    with patch("libs.webfetch.service.WebMarkdownService") as MockService:
        instance = MockService.create.return_value
        instance.fetch_as_markdown.side_effect = Exception("fail")
        
        # We're expecting an exception to be raised, so use pytest.raises
        with pytest.raises(Exception, match="fail"):
            await tool.run("http://fail.com")


def test_placeholder():
    """This test is just here to ensure pytest doesn't complain when all other tests are skipped."""
    assert True
