import pytest
from tools.write_file import WriteFile
from unittest.mock import patch, MagicMock


def test_write_file_run_success():
    tool = WriteFile()
    with patch("libs.fileops.file.FileService") as MockService:
        instance = MockService.return_value
        out = tool.run("/tmp", "file.txt", "data")
        assert out["success"] is True
        assert out["filename"] == "file.txt"
        assert out["base_dir"] == "/tmp"


def test_write_file_run_failure():
    tool = WriteFile()
    with patch("libs.fileops.file.FileService") as MockService:
        instance = MockService.return_value
        instance.write_to_file.side_effect = Exception("fail")
        out = tool.run("/tmp", "file.txt", "data")
        assert out["success"] is False
        assert out["filename"] == "file.txt"
        assert out["base_dir"] == "/tmp"
        assert "Failed to write to file" in out["message"]


def test_write_file_run_absolute_path():
    tool = WriteFile()
    with patch("libs.fileops.file.FileService") as MockService:
        instance = MockService.return_value
        instance.write_to_file.side_effect = ValueError("Absolute paths not allowed")
        out = tool.run("/tmp", "/etc/passwd", "bad")
        assert out["success"] is False
        assert out["filename"] == "/etc/passwd"
        assert "Failed to write to file" in out["message"]


def test_placeholder():
    assert True
