import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

# Import WriteFile class
from tools.write_file import WriteFile


@pytest.mark.asyncio
async def test_write_file_run_success():
    """Test the WriteFile tool with a successful file write."""
    # Create a mock for the FileService
    with patch('libs.fileops.file.FileService') as MockFileService:
        # Set up the mock
        mock_service_instance = MagicMock()
        mock_service_instance.write_to_file.return_value = True
        MockFileService.return_value = mock_service_instance
        
        # Create an instance of WriteFile and run it
        tool = WriteFile("write_file")  # Provide required name parameter
        result = await tool.run(base_dir="/tmp", filename="output.txt", content="Test content")
        
        # Verify the result matches actual implementation
        assert result["success"] is True
        assert "Successfully wrote content" in result["result"]
        assert result["filename"] == "output.txt"
        assert result["base_dir"] == "/tmp"
        
        # Verify that write_to_file was called with the expected arguments
        mock_service_instance.write_to_file.assert_called_once_with("output.txt", "Test content")


@pytest.mark.asyncio
async def test_write_file_run_failure():
    """Test the WriteFile tool when the file cannot be written."""
    # Create a mock for the FileService that raises an exception
    with patch('libs.fileops.file.FileService') as MockFileService:
        # Set up the mock
        mock_service_instance = MagicMock()
        mock_service_instance.write_to_file.side_effect = Exception("Write error")
        MockFileService.return_value = mock_service_instance
        
        # Create an instance of WriteFile and run it
        tool = WriteFile("write_file")  # Provide required name parameter
        result = await tool.run(base_dir="/tmp", filename="output.txt", content="Test content")
        
        # Verify the result matches actual implementation
        assert result["success"] is False
        assert "Failed to write to file" in result["result"]
        assert "Write error" in result["result"]
        assert result["filename"] == "output.txt"
        assert result["base_dir"] == "/tmp"


@pytest.mark.asyncio
async def test_write_file_run_absolute_path():
    """Test the WriteFile tool with an absolute path."""
    # Create a mock for the FileService
    with patch('libs.fileops.file.FileService') as MockFileService:
        # Set up the mock
        mock_service_instance = MagicMock()
        mock_service_instance.write_to_file.return_value = True
        MockFileService.return_value = mock_service_instance
        
        # Create an instance of WriteFile and run it
        tool = WriteFile("write_file")  # Provide required name parameter
        # Use an absolute path that should be handled by the FileService
        absolute_path = "/absolute/path/file.txt"
        result = await tool.run(base_dir="/tmp", filename=absolute_path, content="Absolute path")
        
        # Verify the result matches actual implementation
        assert result["success"] is True
        assert "Successfully wrote content" in result["result"]
        assert result["filename"] == absolute_path
        
        # Verify that write_to_file was called with the correct parameters
        mock_service_instance.write_to_file.assert_called_once_with(absolute_path, "Absolute path")


def test_placeholder():
    """This test is just here to ensure pytest doesn't complain when all other tests are skipped."""
    assert True
