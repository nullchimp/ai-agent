"""
Tests for the read_file.py tool
"""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))


def test_read_file_initialization():
    """Test that ReadFile class initializes correctly."""
    from tools.read_file import ReadFile
    
    # Initialize with a name
    tool = ReadFile("read_file_tool")
    
    # Verify name is set
    assert tool.name == "read_file_tool"
    
    # Verify schema structure via define() method
    schema = tool.define()
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "read_file_tool"
    assert "description" in schema["function"]
    assert "parameters" in schema["function"]
    
    # Check required parameters
    params = schema["function"]["parameters"]
    assert "base_dir" in params["properties"]
    assert "filename" in params["properties"]
    assert "base_dir" in params["required"]
    assert "filename" in params["required"]


@pytest.mark.asyncio
async def test_read_file_success():
    """Test successful execution of ReadFile."""
    from tools.read_file import ReadFile
    
    # Create a mock for FileService
    with patch('libs.fileops.file.FileService') as MockFileService:
        # Configure the mock
        mock_service_instance = MagicMock()
        mock_service_instance.read_file.return_value = "File content"
        MockFileService.return_value = mock_service_instance
        
        # Create tool and execute
        tool = ReadFile("read_file")
        result = await tool.run(base_dir="/base", filename="test.txt")
        
        # Verify FileService was created with correct base_dir
        MockFileService.assert_called_once_with("/base")
        
        # Verify read_file was called with correct filename
        mock_service_instance.read_file.assert_called_once_with("test.txt")
        
        # Verify result structure
        assert result["success"] is True
        assert "Successfully read content" in result["result"]
        assert result["filename"] == "test.txt"
        assert result["base_dir"] == "/base"
        assert result["content"] == "File content"


@pytest.mark.asyncio
async def test_read_file_error():
    """Test ReadFile when an error occurs."""
    from tools.read_file import ReadFile
    
    # Create a mock for FileService
    with patch('libs.fileops.file.FileService') as MockFileService:
        # Configure the mock to raise an exception
        mock_service_instance = MagicMock()
        mock_service_instance.read_file.side_effect = FileNotFoundError("File not found")
        MockFileService.return_value = mock_service_instance
        
        # Create tool and execute
        tool = ReadFile("read_file")
        result = await tool.run(base_dir="/base", filename="nonexistent.txt")
        
        # Verify FileService was created with correct base_dir
        MockFileService.assert_called_once_with("/base")
        
        # Verify read_file was called with correct filename
        mock_service_instance.read_file.assert_called_once_with("nonexistent.txt")
        
        # Verify result structure for error case
        assert result["success"] is False
        assert "Failed to read file" in result["result"]
        assert "File not found" in result["result"]
        assert result["filename"] == "nonexistent.txt"
        assert result["base_dir"] == "/base"
        assert result["content"] is None


@pytest.mark.asyncio
async def test_read_file_with_relative_path():
    """Test ReadFile with a relative path."""
    from tools.read_file import ReadFile
    
    # Create a mock for FileService
    with patch('libs.fileops.file.FileService') as MockFileService:
        # Configure the mock
        mock_service_instance = MagicMock()
        mock_service_instance.read_file.return_value = "Directory content"
        MockFileService.return_value = mock_service_instance
        
        # Create tool and execute with relative path
        tool = ReadFile("read_file")
        result = await tool.run(base_dir="./base", filename="subdir/file.txt")
        
        # Verify FileService was created with correct base_dir
        MockFileService.assert_called_once_with("./base")
        
        # Verify read_file was called with correct path
        mock_service_instance.read_file.assert_called_once_with("subdir/file.txt")
        
        # Verify result
        assert result["success"] is True
        assert result["content"] == "Directory content"
