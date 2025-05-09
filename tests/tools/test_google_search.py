import pytest
from tools.google_search import GoogleSearch
from tools.read_file import ReadFile
from tools.write_file import WriteFile
from tools.list_files import ListFiles
from tools.web_fetch import WebFetch
from unittest.mock import patch, MagicMock


def test_google_search_run_success(monkeypatch):
    tool = GoogleSearch()
    mock_service = MagicMock()
    mock_results = MagicMock()
    mock_results.query = "q"
    mock_results.total_results = 1
    mock_results.search_time = 0.1
    mock_results.results = [MagicMock()]
    mock_results.formatted_count = "1"
    mock_results.results[0].__str__.return_value = "result"
    monkeypatch.setattr("libs.search.service.Service.create", lambda: mock_service)
    mock_service.search.return_value = mock_results
    out = tool.run("q", 1)
    assert out["query"] == "q"
    assert out["total_results"] == 1
    assert out["results"] == ["result"]


def test_read_file_run_success():
    tool = ReadFile()
    with patch("libs.fileops.file.FileService") as MockService:
        instance = MockService.return_value
        instance.read_file.return_value = "data"
        out = tool.run("/tmp", "file.txt")
        assert out["success"] is True
        assert out["content"] == "data"


def test_read_file_run_failure():
    tool = ReadFile()
    with patch("libs.fileops.file.FileService") as MockService:
        instance = MockService.return_value
        instance.read_file.side_effect = Exception("fail")
        out = tool.run("/tmp", "file.txt")
        assert out["success"] is False
        assert out["content"] is None


def test_write_file_run_success():
    tool = WriteFile()
    with patch("libs.fileops.file.FileService") as MockService:
        instance = MockService.return_value
        out = tool.run("/tmp", "file.txt", "data")
        assert out["success"] is True
        assert out["filename"] == "file.txt"


def test_write_file_run_failure():
    tool = WriteFile()
    with patch("libs.fileops.file.FileService") as MockService:
        instance = MockService.return_value
        instance.write_to_file.side_effect = Exception("fail")
        out = tool.run("/tmp", "file.txt", "data")
        assert out["success"] is False
        assert out["filename"] == "file.txt"


def test_list_files_run_success():
    tool = ListFiles()
    with patch("libs.fileops.file.FileService") as MockService:
        instance = MockService.return_value
        instance.list_files.return_value = ["a.txt"]
        out = tool.run("/tmp", ".")
        assert out["success"] is True
        assert out["files"] == ["a.txt"]


def test_list_files_run_failure():
    tool = ListFiles()
    with patch("libs.fileops.file.FileService") as MockService:
        instance = MockService.return_value
        instance.list_files.side_effect = Exception("fail")
        out = tool.run("/tmp", ".")
        assert out["success"] is False
        assert out["files"] == []


def test_web_fetch_run():
    tool = WebFetch()
    with patch("libs.webfetch.service.WebMarkdownService") as MockService:
        instance = MockService.create.return_value
        instance.fetch_as_markdown.return_value = ("md", 200)
        out = tool.run("http://x.com", headers={"A": "B"})
        assert out["url"] == "http://x.com"
        assert out["status_code"] == 200
        assert out["markdown_content"] == "md"
