import pytest
from tools.list_files import ListFiles
from unittest.mock import patch, MagicMock


def test_list_files_run_success():
    tool = ListFiles()
    with patch("libs.fileops.file.FileService") as MockService:
        instance = MockService.return_value
        instance.list_files.return_value = ["a.txt", "b.txt"]
        out = tool.run("/tmp", ".")
        assert out["success"] is True
        assert out["files"] == ["a.txt", "b.txt"]
        assert out["base_dir"] == "/tmp"
        assert out["directory"] == "."


def test_list_files_run_failure():
    tool = ListFiles()
    with patch("libs.fileops.file.FileService") as MockService:
        instance = MockService.return_value
        instance.list_files.side_effect = Exception("fail")
        out = tool.run("/tmp", ".")
        assert out["success"] is False
        assert out["files"] == []
        assert out["base_dir"] == "/tmp"
        assert out["directory"] == "."
        assert "Failed to list files" in out["message"]


def test_list_files_run_directory_not_found():
    tool = ListFiles()
    with patch("libs.fileops.file.FileService") as MockService:
        instance = MockService.return_value
        instance.list_files.side_effect = FileNotFoundError("not found")
        out = tool.run("/tmp", "notadir")
        assert out["success"] is False
        assert out["files"] == []
        assert out["directory"] == "notadir"
        assert "Failed to list files" in out["message"]


def test_placeholder():
    assert True
