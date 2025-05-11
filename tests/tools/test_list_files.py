import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from tools.list_files import ListFiles


@pytest.mark.asyncio
async def test_list_files_run_success():
    tool = ListFiles()
    with patch("libs.fileops.file.FileService") as MockService:
        instance = MockService.return_value
        instance.list_files.return_value = ["a.txt", "b.txt"]
        out = await tool.run("/tmp", ".")
        assert out["success"] is True
        assert out["files"] == ["a.txt", "b.txt"]
        assert out["directory"] == "."
        assert out["base_dir"] == "/tmp"
        instance.list_files.assert_called_with(".")


@pytest.mark.asyncio
async def test_list_files_run_failure():
    tool = ListFiles()
    with patch("libs.fileops.file.FileService") as MockService:
        instance = MockService.return_value
        instance.list_files.side_effect = Exception("fail")
        out = await tool.run("/tmp", ".")
        assert out["success"] is False
        assert "fail" in out["message"]
        assert out["directory"] == "."
        assert out["files"] == []
        instance.list_files.assert_called_with(".")


@pytest.mark.asyncio
async def test_list_files_run_directory_not_found():
    tool = ListFiles()
    with patch("libs.fileops.file.FileService") as MockService:
        instance = MockService.return_value
        instance.list_files.side_effect = FileNotFoundError("not found")
        out = await tool.run("/tmp", "notadir")
        assert out["success"] is False
        assert "not found" in out["message"]
        assert out["directory"] == "notadir"
        assert out["files"] == []
        instance.list_files.assert_called_with("notadir")


def test_placeholder():
    """This test is just here to ensure pytest doesn't complain when all other tests are skipped."""
    assert True
