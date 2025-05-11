import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

# Import ReadFile class
from tools.read_file import ReadFile


@pytest.mark.asyncio
async def test_read_file_run_success():
    """Test the ReadFile tool with a successful file read."""
    # Create a mock for the FileService
    with patch('libs.fileops.file.FileService') as MockFileService:
        # Set up the mock service
        mock_service_instance = MagicMock()
        mock_service_instance.read_file.return_value = "Test file content"
        MockFileService.return_value = mock_service_instance
        
        # Create an instance of ReadFile and run it
        tool = ReadFile("read_file")  # Provide required name parameter
        result = await tool.run(base_dir="/tmp", filename="test.txt")
        
        # Verify the result matches actual implementation
        assert result["success"] is True
        assert result["content"] == "Test file content"
        assert "Successfully read content" in result["result"]
        
        # Verify that read_file was called with the expected arguments
        mock_service_instance.read_file.assert_called_once_with("test.txt")


@pytest.mark.asyncio
async def test_read_file_run_failure():
    """Test the ReadFile tool when the file cannot be read."""
    # Create a mock for the FileService that raises an exception
    with patch('libs.fileops.file.FileService') as MockFileService:
        # Set up the mock
        mock_service_instance = MagicMock()
        mock_service_instance.read_file.side_effect = Exception("File error")
        MockFileService.return_value = mock_service_instance
        
        # Create an instance of ReadFile and run it
        tool = ReadFile("read_file")  # Provide required name parameter
        result = await tool.run(base_dir="/tmp", filename="nonexistent.txt")
        
        # Verify the result matches actual implementation
        assert result["success"] is False
        assert "Failed to read file" in result["result"]
        assert "File error" in result["result"]
        assert result["content"] is None


@pytest.mark.asyncio
async def test_read_file_run_not_found():
    """Test the ReadFile tool with a file that doesn't exist."""
    # Create a mock for the FileService that raises a FileNotFoundError
    with patch('libs.fileops.file.FileService') as MockFileService:
        # Set up the mock
        mock_service_instance = MagicMock()
        mock_service_instance.read_file.side_effect = FileNotFoundError("File not found")
        MockFileService.return_value = mock_service_instance
        
        # Create an instance of ReadFile and run it
        tool = ReadFile("read_file")  # Provide required name parameter
        result = await tool.run(base_dir="/nonexistent", filename="nonexistent.txt")
        
        # Verify the result matches actual implementation
        assert result["success"] is False
        assert "Failed to read file" in result["result"]
        assert "not found" in result["result"].lower()
        assert result["content"] is None


def test_placeholder():
    """This test is just here to ensure pytest doesn't complain when all other tests are skipped."""
    assert True
