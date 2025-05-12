"""
Tests for the write_file.py tool
"""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))


def test_write_file_initialization():
    """Test that WriteFile class initializes correctly."""
    from tools.write_file import WriteFile
    
    # Initialize with a name
    tool = WriteFile("write_file_tool")
    
    # Verify name is set
    assert tool.name == "write_file_tool"
    
    # Verify schema structure via define() method
    schema = tool.define()
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "write_file_tool"
    assert "description" in schema["function"]
    assert "parameters" in schema["function"]
    
    # Check required parameters
    params = schema["function"]["parameters"]
    assert "base_dir" in params["properties"]
    assert "filename" in params["properties"]
    assert "content" in params["properties"]
    assert "base_dir" in params["required"]
    assert "filename" in params["required"]
    assert "content" in params["required"]


@pytest.mark.asyncio
async def test_write_file_success():
    """Test successful execution of WriteFile."""
    from tools.write_file import WriteFile
    
    # Create a mock for FileService
    with patch('libs.fileops.file.FileService') as MockFileService:
        # Configure the mock
        mock_service_instance = MagicMock()
        MockFileService.return_value = mock_service_instance
        
        # Create tool and execute
        tool = WriteFile("write_file")
        result = await tool.run(base_dir="/base", filename="test.txt", content="Test content")
        
        # Verify FileService was created with correct base_dir
        MockFileService.assert_called_once_with("/base")
        
        # Verify write_to_file was called with correct parameters
        mock_service_instance.write_to_file.assert_called_once_with("test.txt", "Test content")
        
        # Verify result structure
        assert result["success"] is True
        assert "Successfully wrote content" in result["result"]
        assert result["filename"] == "test.txt"
        assert result["base_dir"] == "/base"


@pytest.mark.asyncio
async def test_write_file_error():
    """Test WriteFile when an error occurs."""
    from tools.write_file import WriteFile
    
    # Create a mock for FileService
    with patch('libs.fileops.file.FileService') as MockFileService:
        # Configure the mock to raise an exception
        mock_service_instance = MagicMock()
        mock_service_instance.write_to_file.side_effect = PermissionError("Permission denied")
        MockFileService.return_value = mock_service_instance
        
        # Create tool and execute
        tool = WriteFile("write_file")
        result = await tool.run(base_dir="/base", filename="protected.txt", content="Test content")
        
        # Verify FileService was created with correct base_dir
        MockFileService.assert_called_once_with("/base")
        
        # Verify write_to_file was called with correct parameters
        mock_service_instance.write_to_file.assert_called_once_with("protected.txt", "Test content")
        
        # Verify result structure for error case
        assert result["success"] is False
        assert "Failed to write to file" in result["result"]
        assert "Permission denied" in result["result"]
        assert result["filename"] == "protected.txt"
        assert result["base_dir"] == "/base"


@pytest.mark.asyncio
async def test_write_file_with_directory_creation():
    """Test WriteFile with a path that requires directory creation."""
    from tools.write_file import WriteFile
    
    # Create a mock for FileService
    with patch('libs.fileops.file.FileService') as MockFileService:
        # Configure the mock
        mock_service_instance = MagicMock()
        MockFileService.return_value = mock_service_instance
        
        # Create tool and execute with path containing directories
        tool = WriteFile("write_file")
        result = await tool.run(base_dir="./base", filename="subdir/nested/file.txt", content="Nested content")
        
        # Verify FileService was created with correct base_dir
        MockFileService.assert_called_once_with("./base")
        
        # Verify write_to_file was called with correct parameters
        mock_service_instance.write_to_file.assert_called_once_with("subdir/nested/file.txt", "Nested content")
        
        # Verify result
        assert result["success"] is True
        assert "Successfully wrote content" in result["result"]
