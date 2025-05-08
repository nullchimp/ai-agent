"""
Module for converting HTML content to Markdown.
"""
import html2text
from typing import Optional


class HtmlToMarkdownConverter:
    """
    Service for converting HTML content to Markdown format.
    """

    @staticmethod
    def create() -> "HtmlToMarkdownConverter":
        return HtmlToMarkdownConverter()

    def __init__(self) -> None:
        self.converter = self._create_converter()

    def _create_converter(self) -> html2text.HTML2Text:
        h = html2text.HTML2Text()
        h.body_width = 100
        h.ignore_links = True
        h.ignore_images = True
        h.ignore_emphasis = True
        h.ignore_tables = True
        h.ignore_mailto_links = True
        return h

    def convert(self, html_content: str) -> str:
        return self.converter.handle(html_content)