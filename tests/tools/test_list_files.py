"""
Tests for the list_files.py tool
"""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock
from typing import Optional

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))


def test_list_files_initialization():
    """Test that ListFiles class initializes correctly."""
    from tools.list_files import ListFiles
    
    # Initialize with a name
    tool = ListFiles("list_files_tool")
    
    # Verify name is set
    assert tool.name == "list_files_tool"
    
    # Verify schema structure via define() method
    schema = tool.define()
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "list_files_tool"
    assert "description" in schema["function"]
    assert "parameters" in schema["function"]
    
    # Check required parameters
    params = schema["function"]["parameters"]
    assert "base_dir" in params["properties"]
    assert "directory" in params["properties"]
    assert "base_dir" in params["required"]
    assert "directory" not in params["required"]  # directory is optional


@pytest.mark.asyncio
async def test_list_files_success_default_directory():
    """Test successful execution of ListFiles with default directory."""
    from tools.list_files import ListFiles
    
    # Create a mock for FileService
    with patch('libs.fileops.file.FileService') as MockFileService:
        # Configure the mock
        mock_service_instance = MagicMock()
        mock_service_instance.list_files.return_value = ["file1.txt", "file2.txt", "subdir/"]
        MockFileService.return_value = mock_service_instance
        
        # Create tool and execute with default directory
        tool = ListFiles("list_files")
        result = await tool.run(base_dir="/base")
        
        # Verify FileService was created with correct base_dir
        MockFileService.assert_called_once_with("/base")
        
        # Verify list_files was called with default directory
        mock_service_instance.list_files.assert_called_once_with(".")
        
        # Verify result structure
        assert result["success"] is True
        assert "Successfully listed files" in result["result"]
        assert result["base_dir"] == "/base"
        assert result["directory"] == "."
        assert len(result["files"]) == 3
        assert "file1.txt" in result["files"]
        assert "file2.txt" in result["files"]
        assert "subdir/" in result["files"]


@pytest.mark.asyncio
async def test_list_files_success_custom_directory():
    """Test successful execution of ListFiles with custom directory."""
    from tools.list_files import ListFiles
    
    # Create a mock for FileService
    with patch('libs.fileops.file.FileService') as MockFileService:
        # Configure the mock
        mock_service_instance = MagicMock()
        mock_service_instance.list_files.return_value = ["subfile1.txt", "subfile2.txt"]
        MockFileService.return_value = mock_service_instance
        
        # Create tool and execute with custom directory
        tool = ListFiles("list_files")
        result = await tool.run(base_dir="/base", directory="subdir")
        
        # Verify FileService was created with correct base_dir
        MockFileService.assert_called_once_with("/base")
        
        # Verify list_files was called with custom directory
        mock_service_instance.list_files.assert_called_once_with("subdir")
        
        # Verify result structure
        assert result["success"] is True
        assert "Successfully listed files in subdir" in result["result"]
        assert result["base_dir"] == "/base"
        assert result["directory"] == "subdir"
        assert len(result["files"]) == 2
        assert "subfile1.txt" in result["files"]
        assert "subfile2.txt" in result["files"]


@pytest.mark.asyncio
async def test_list_files_empty_directory():
    """Test ListFiles with an empty directory."""
    from tools.list_files import ListFiles
    
    # Create a mock for FileService
    with patch('libs.fileops.file.FileService') as MockFileService:
        # Configure the mock to return empty list
        mock_service_instance = MagicMock()
        mock_service_instance.list_files.return_value = []
        MockFileService.return_value = mock_service_instance
        
        # Create tool and execute
        tool = ListFiles("list_files")
        result = await tool.run(base_dir="/base", directory="empty_dir")
        
        # Verify FileService was created with correct base_dir
        MockFileService.assert_called_once_with("/base")
        
        # Verify list_files was called with correct directory
        mock_service_instance.list_files.assert_called_once_with("empty_dir")
        
        # Verify result structure
        assert result["success"] is True
        assert len(result["files"]) == 0
        assert result["directory"] == "empty_dir"


@pytest.mark.asyncio
async def test_list_files_error():
    """Test ListFiles when an error occurs."""
    from tools.list_files import ListFiles
    
    # Create a mock for FileService
    with patch('libs.fileops.file.FileService') as MockFileService:
        # Configure the mock to raise an exception
        mock_service_instance = MagicMock()
        mock_service_instance.list_files.side_effect = FileNotFoundError("Directory not found")
        MockFileService.return_value = mock_service_instance
        
        # Create tool and execute
        tool = ListFiles("list_files")
        result = await tool.run(base_dir="/base", directory="nonexistent")
        
        # Verify FileService was created with correct base_dir
        MockFileService.assert_called_once_with("/base")
        
        # Verify list_files was called with correct directory
        mock_service_instance.list_files.assert_called_once_with("nonexistent")
        
        # Verify result structure for error case
        assert result["success"] is False
        assert "Failed to list files" in result["result"]
        assert "Directory not found" in result["result"]
        assert result["base_dir"] == "/base"
        assert result["directory"] == "nonexistent"
        assert result["files"] == []
