import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from tools.write_file import WriteFile


@pytest.mark.asyncio
async def test_write_file_run_success():
    tool = WriteFile()
    with patch("libs.fileops.file.FileService") as MockService:
        instance = MockService.return_value
        out = await tool.run("/tmp", "file.txt", "data")
        assert out["success"] is True
        assert out["filename"] == "file.txt"
        assert out["base_dir"] == "/tmp"
        instance.write_to_file.assert_called_with("file.txt", "data")


@pytest.mark.asyncio
async def test_write_file_run_failure():
    tool = WriteFile()
    with patch("libs.fileops.file.FileService") as MockService:
        instance = MockService.return_value
        instance.write_to_file.side_effect = Exception("fail")
        out = await tool.run("/tmp", "file.txt", "data")
        assert out["success"] is False
        assert "fail" in out["message"]
        assert out["filename"] == "file.txt"
        instance.write_to_file.assert_called_with("file.txt", "data")


@pytest.mark.asyncio
async def test_write_file_run_absolute_path():
    tool = WriteFile()
    with patch("libs.fileops.file.FileService") as MockService:
        instance = MockService.return_value
        instance.write_to_file.side_effect = ValueError("Absolute paths not allowed")
        out = await tool.run("/tmp", "/etc/passwd", "bad")
        assert out["success"] is False
        assert "not allowed" in out["message"]
        assert out["filename"] == "/etc/passwd"
        instance.write_to_file.assert_called_with("/etc/passwd", "bad")


def test_placeholder():
    """This test is just here to ensure pytest doesn't complain when all other tests are skipped."""
    assert True
