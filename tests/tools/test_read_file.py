import pytest
from tools.read_file import ReadFile
from unittest.mock import patch, MagicMock


def test_read_file_run_success():
    tool = ReadFile()
    with patch("libs.fileops.file.FileService") as MockService:
        instance = MockService.return_value
        instance.read_file.return_value = "data"
        out = tool.run("/tmp", "file.txt")
        assert out["success"] is True
        assert out["content"] == "data"
        assert out["filename"] == "file.txt"
        assert out["base_dir"] == "/tmp"


def test_read_file_run_failure():
    tool = ReadFile()
    with patch("libs.fileops.file.FileService") as MockService:
        instance = MockService.return_value
        instance.read_file.side_effect = Exception("fail")
        out = tool.run("/tmp", "file.txt")
        assert out["success"] is False
        assert out["content"] is None
        assert out["filename"] == "file.txt"
        assert out["base_dir"] == "/tmp"
        assert "Failed to read file" in out["message"]


def test_read_file_run_not_found():
    tool = ReadFile()
    with patch("libs.fileops.file.FileService") as MockService:
        instance = MockService.return_value
        instance.read_file.side_effect = FileNotFoundError("not found")
        out = tool.run("/tmp", "nofile.txt")
        assert out["success"] is False
        assert out["content"] is None
        assert out["filename"] == "nofile.txt"
        assert "Failed to read file" in out["message"]


def test_placeholder():
    assert True
