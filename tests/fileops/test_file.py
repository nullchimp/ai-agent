"""
Tests for file operations module.
"""
import os
import tempfile
from pathlib import Path
import pytest

from src.fileops.file import FileService


@pytest.fixture
def temp_base_dir():
    """Create a temporary base directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


def test_init_creates_base_dir():
    """Test that the base directory is created if it doesn't exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        nonexistent_dir = os.path.join(temp_dir, "nonexistent")
        assert not os.path.exists(nonexistent_dir)
        
        FileService(nonexistent_dir)
        assert os.path.exists(nonexistent_dir)


def test_write_and_read_file(temp_base_dir):
    """Test writing to and reading from a file."""
    service = FileService(temp_base_dir)
    
    # Write content to a file
    test_content = "Hello, world!"
    service.write_to_file("test.txt", test_content)
    
    # Read back the content
    read_content = service.read_file("test.txt")
    
    assert read_content == test_content
    assert os.path.exists(os.path.join(temp_base_dir, "test.txt"))


def test_write_and_read_file_in_subdirectory(temp_base_dir):
    """Test writing to and reading from a file in a subdirectory."""
    service = FileService(temp_base_dir)
    
    # Write content to a file in a subdirectory
    test_content = "Hello, subdirectory!"
    service.write_to_file("subdir/test.txt", test_content)
    
    # Read back the content
    read_content = service.read_file("subdir/test.txt")
    
    assert read_content == test_content
    assert os.path.exists(os.path.join(temp_base_dir, "subdir", "test.txt"))


def test_read_nonexistent_file(temp_base_dir):
    """Test reading a nonexistent file raises FileNotFoundError."""
    service = FileService(temp_base_dir)
    
    with pytest.raises(FileNotFoundError):
        service.read_file("nonexistent.txt")


def test_list_files(temp_base_dir):
    """Test listing files in a directory."""
    service = FileService(temp_base_dir)
    
    # Create test files
    for i in range(3):
        service.write_to_file(f"test{i}.txt", f"Content {i}")
    
    # List files
    files = service.list_files(".")
    
    # Verify all files are listed
    assert len(files) == 3
    assert "test0.txt" in files
    assert "test1.txt" in files
    assert "test2.txt" in files


def test_list_files_in_subdirectory(temp_base_dir):
    """Test listing files in a subdirectory."""
    service = FileService(temp_base_dir)
    
    # Create subdirectory and files
    subdir = "subdir"
    os.makedirs(os.path.join(temp_base_dir, subdir))
    
    for i in range(2):
        service.write_to_file(f"{subdir}/subtest{i}.txt", f"Subdir content {i}")
    
    # List files in subdirectory
    files = service.list_files(subdir)
    
    # Verify files in subdirectory are listed
    assert len(files) == 2
    assert "subtest0.txt" in files
    assert "subtest1.txt" in files


def test_list_nonexistent_directory(temp_base_dir):
    """Test listing files in a nonexistent directory raises FileNotFoundError."""
    service = FileService(temp_base_dir)
    
    with pytest.raises(FileNotFoundError):
        service.list_files("nonexistent")


def test_secure_path_prevents_directory_traversal(temp_base_dir):
    """Test that the secure path logic prevents directory traversal attacks."""
    service = FileService(temp_base_dir)
    
    # Create a file in the base directory
    service.write_to_file("safe.txt", "Safe content")
    
    # Try to read a file outside the base directory through directory traversal
    traversal_path = "../" * 10 + "etc/passwd"
    
    # This should not raise an error but should read from base_dir/passwd instead
    with pytest.raises(FileNotFoundError):
        service.read_file(traversal_path)
    
    # The operation should have been sanitized to just the filename
    assert not os.path.exists(os.path.join(temp_base_dir, "passwd"))


def test_secure_path_handles_absolute_paths(temp_base_dir):
    """Test that the secure path logic handles absolute paths correctly."""
    service = FileService(temp_base_dir)
    
    # Try to use an absolute path - should raise ValueError
    with pytest.raises(ValueError):
        service.write_to_file("/absolute/path.txt", "Should not work")


def test_secure_path_normalizes_paths(temp_base_dir):
    """Test path normalization in secure path logic."""
    service = FileService(temp_base_dir)
    
    # Write content using a path with unnecessary components
    test_content = "Normal path content"
    service.write_to_file("./test/../test/./path.txt", test_content)
    
    # Read it back using the normalized path
    read_content = service.read_file("test/path.txt")
    
    assert read_content == test_content