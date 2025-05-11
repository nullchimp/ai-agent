import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

# Import ListFiles class
from tools.list_files import ListFiles


@pytest.mark.asyncio
async def test_list_files_run_success():
    """Test the ListFiles tool with a successful directory listing."""
    # Create a mock for the FileService
    with patch('libs.fileops.file.FileService') as MockFileService:
        # Set up the mock
        mock_service_instance = MagicMock()
        mock_files = ["file1.txt", "file2.txt", "dir1/file3.txt"]
        mock_service_instance.list_files.return_value = mock_files
        MockFileService.return_value = mock_service_instance
        
        # Create an instance of ListFiles and run it
        tool = ListFiles("list_files")  # Provide required name parameter
        result = await tool.run(base_dir="/tmp")
        
        # Verify the result matches actual implementation
        assert result["success"] is True
        assert "Successfully listed files" in result["result"]
        assert result["files"] == mock_files
        assert len(result["files"]) == 3
        assert result["base_dir"] == "/tmp"
        assert result["directory"] == "."
        
        # Verify that list_files was called with the expected arguments
        mock_service_instance.list_files.assert_called_once_with(".")


@pytest.mark.asyncio
async def test_list_files_run_failure():
    """Test the ListFiles tool with a general failure."""
    # Create a mock for the FileService that raises an exception
    with patch('libs.fileops.file.FileService') as MockFileService:
        # Set up the mock
        mock_service_instance = MagicMock()
        mock_service_instance.list_files.side_effect = Exception("General directory error")
        MockFileService.return_value = mock_service_instance
        
        # Create an instance of ListFiles and run it
        tool = ListFiles("list_files")  # Provide required name parameter
        result = await tool.run(base_dir="/tmp")
        
        # Verify the result matches actual implementation
        assert result["success"] is False
        assert "Failed to list files" in result["result"]
        assert "General directory error" in result["result"]
        assert result["files"] == []
        assert result["base_dir"] == "/tmp"


@pytest.mark.asyncio
async def test_list_files_run_directory_not_found():
    """Test the ListFiles tool with a directory that doesn't exist."""
    # Create a mock for the FileService that raises a specific exception for directory not found
    with patch('libs.fileops.file.FileService') as MockFileService:
        # Set up the mock
        mock_service_instance = MagicMock()
        mock_service_instance.list_files.side_effect = FileNotFoundError("Directory not found")
        MockFileService.return_value = mock_service_instance
        
        # Create an instance of ListFiles and run it
        tool = ListFiles("list_files")  # Provide required name parameter
        result = await tool.run(base_dir="/nonexistent")
        
        # Verify the result matches actual implementation
        assert result["success"] is False
        assert "Failed to list files" in result["result"]
        assert "not found" in result["result"].lower()
        assert result["files"] == []
        assert result["base_dir"] == "/nonexistent"


def test_placeholder():
    """This test is just here to ensure pytest doesn't complain when all other tests are skipped."""
    assert True
