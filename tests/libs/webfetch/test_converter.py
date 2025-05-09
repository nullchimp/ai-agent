import pytest
from libs.webfetch.converter import HtmlToMarkdownConverter


@pytest.fixture
def converter():
    return HtmlToMarkdownConverter.create()


def test_convert_html_to_markdown(converter):
    html = "<h1>Title</h1><p>Hello <b>world</b></p>"
    md = converter.convert(html)
    assert "Title" in md
    assert "Hello" in md
    assert "world" in md


def test_convert_html_to_markdown_basic():
    converter = HtmlToMarkdownConverter.create()
    html = "<h2>Header</h2><p>Body <b>bold</b></p>"
    md = converter.convert(html)
    assert "Header" in md
    assert "Body" in md
    assert "bold" in md


def test_convert_html_to_markdown_empty():
    converter = HtmlToMarkdownConverter.create()
    md = converter.convert("")
    assert md.strip() == ""


def test_converter_ignore_links_and_images():
    converter = HtmlToMarkdownConverter.create()
    html = '<a href="http://x">link</a><img src="img.png">'
    md = converter.convert(html)
    assert "link" in md
    assert "http" not in md  # links ignored
    assert "img.png" not in md  # images ignored


def test_converter_instance():
    c = HtmlToMarkdownConverter()
    assert hasattr(c, "converter")


def test_converter_create():
    c = HtmlToMarkdownConverter.create()
    assert isinstance(c, HtmlToMarkdownConverter)


def test_converter_instance_and_create():
    c1 = HtmlToMarkdownConverter()
    c2 = HtmlToMarkdownConverter.create()
    assert isinstance(c1, HtmlToMarkdownConverter)
    assert isinstance(c2, HtmlToMarkdownConverter)
    assert hasattr(c1, "converter")
    assert hasattr(c2, "converter")


def test_converter_handles_tables_and_emphasis():
    converter = HtmlToMarkdownConverter.create()
    html = "<table><tr><td>cell</td></tr></table><em>em</em>"
    md = converter.convert(html)
    assert "cell" in md
    assert "em" in md
    # Should not have markdown table or emphasis syntax
    assert "|" not in md
    assert "*em*" not in md
