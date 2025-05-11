import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from tools.read_file import ReadFile


@pytest.mark.asyncio
async def test_read_file_run_success():
    tool = ReadFile()
    with patch("libs.fileops.file.FileService") as MockService:
        instance = MockService.return_value
        instance.read_file.return_value = "data"
        out = await tool.run("/tmp", "file.txt")
        assert out["success"] is True
        assert out["content"] == "data"
        assert out["filename"] == "file.txt"
        assert out["base_dir"] == "/tmp"
        instance.read_file.assert_called_with("file.txt")


@pytest.mark.asyncio
async def test_read_file_run_failure():
    tool = ReadFile()
    with patch("libs.fileops.file.FileService") as MockService:
        instance = MockService.return_value
        instance.read_file.side_effect = Exception("fail")
        out = await tool.run("/tmp", "file.txt")
        assert out["success"] is False
        assert "fail" in out["message"]
        assert out["filename"] == "file.txt"
        instance.read_file.assert_called_with("file.txt")


@pytest.mark.asyncio
async def test_read_file_run_not_found():
    tool = ReadFile()
    with patch("libs.fileops.file.FileService") as MockService:
        instance = MockService.return_value
        instance.read_file.side_effect = FileNotFoundError("not found")
        out = await tool.run("/tmp", "nofile.txt")
        assert out["success"] is False
        assert "not found" in out["message"]
        assert out["filename"] == "nofile.txt"
        instance.read_file.assert_called_with("nofile.txt")


def test_placeholder():
    """This test is just here to ensure pytest doesn't complain when all other tests are skipped."""
    assert True
