"""
Module for fetching web content and converting it to Markdown.
"""
from typing import Dict, Optional, Tuple

from .fetch import WebFetcher
from .converter import HtmlToMarkdownConverter


class WebMarkdownService:
    """
    Service for fetching web content and converting it to Markdown.
    """

    @staticmethod
    def create() -> "WebMarkdownService":
        fetcher = WebFetcher.create()
        converter = HtmlToMarkdownConverter.create()
        return WebMarkdownService(fetcher, converter)

    def __init__(self, fetcher: WebFetcher, converter: HtmlToMarkdownConverter) -> None:
        self.fetcher = fetcher
        self.converter = converter

    def fetch_as_markdown(self, url: str, headers: Optional[Dict[str, str]] = None) -> Tuple[str, int]:
        html_content, status_code = self.fetcher.fetch_content(url, headers)
        markdown_content = self.converter.convert(html_content)
        return markdown_content, status_code