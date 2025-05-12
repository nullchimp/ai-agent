"""
Tests for the FileService class in libs/fileops/file.py
"""

import os
import sys
import pytest
import tempfile
import shutil
from unittest.mock import patch, mock_open, MagicMock

# Ensure src/ is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))

from libs.fileops.file import FileService


class TestFileService:
    """Test suite for the FileService class"""
    
    def setup_method(self):
        """Setup test environment before each test"""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """Clean up test environment after each test"""
        # Remove the temporary directory and its contents
        shutil.rmtree(self.temp_dir)
    
    def test_init_existing_directory(self):
        """Test initialization with an existing directory"""
        # Create FileService with the existing temp directory
        service = FileService(self.temp_dir)
        
        # Verify base_dir is set and normalized
        assert service.base_dir == os.path.abspath(self.temp_dir)
    
    def test_init_nonexistent_directory(self):
        """Test initialization with a non-existent directory"""
        # Path to a non-existent directory
        nonexistent_dir = os.path.join(self.temp_dir, "nonexistent")
        
        # Create FileService with a non-existent directory
        service = FileService(nonexistent_dir)
        
        # Verify directory was created
        assert os.path.exists(nonexistent_dir)
        assert service.base_dir == os.path.abspath(nonexistent_dir)
    
    def test_init_fails_on_permission_error(self):
        """Test initialization fails when directory creation raises an exception"""
        with patch('os.makedirs') as mock_makedirs:
            # Configure os.makedirs to raise a permission error
            mock_makedirs.side_effect = PermissionError("Permission denied")
            
            # Verify initialization raises ValueError
            with pytest.raises(ValueError, match="Failed to create base directory"):
                FileService("/path/without/permission")
    
    def test_write_to_file_success(self):
        """Test successful file write operation"""
        service = FileService(self.temp_dir)
        test_filename = "test_file.txt"
        test_content = "This is test content"
        
        # Write content to file
        service.write_to_file(test_filename, test_content)
        
        # Verify file was written correctly
        file_path = os.path.join(self.temp_dir, test_filename)
        assert os.path.exists(file_path)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert content == test_content
    
    def test_write_to_file_creates_directories(self):
        """Test write operation creates intermediate directories"""
        service = FileService(self.temp_dir)
        nested_filename = "nested/dir/structure/test_file.txt"
        test_content = "Nested file content"
        
        # Write content to nested file
        service.write_to_file(nested_filename, test_content)
        
        # Verify directories and file were created
        file_path = os.path.join(self.temp_dir, nested_filename)
        assert os.path.exists(file_path)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert content == test_content
    
    def test_write_to_file_fails_on_io_error(self):
        """Test write operation failure handling"""
        service = FileService(self.temp_dir)
        
        # Mock open to raise IOError
        with patch('builtins.open', side_effect=IOError("IO Error")):
            with pytest.raises(ValueError, match="Failed to write file"):
                service.write_to_file("test.txt", "content")
    
    def test_read_file_success(self):
        """Test successful file read operation"""
        service = FileService(self.temp_dir)
        test_filename = "readable.txt"
        test_content = "This is readable content"
        
        # Create a file to read
        file_path = os.path.join(self.temp_dir, test_filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        # Read the file
        content = service.read_file(test_filename)
        
        # Verify content
        assert content == test_content
    
    def test_read_file_nonexistent(self):
        """Test read operation with non-existent file"""
        service = FileService(self.temp_dir)
        
        with pytest.raises(FileNotFoundError, match="File not found"):
            service.read_file("nonexistent.txt")
    
    def test_read_file_io_error(self):
        """Test read operation failure handling"""
        service = FileService(self.temp_dir)
        test_filename = "error.txt"
        
        # Create an empty file
        file_path = os.path.join(self.temp_dir, test_filename)
        with open(file_path, 'w') as f:
            pass
        
        # Mock open to raise IOError
        with patch('builtins.open', side_effect=IOError("IO Error")):
            with pytest.raises(ValueError, match="Failed to read file"):
                service.read_file(test_filename)
    
    def test_list_files_success(self):
        """Test successful directory listing"""
        service = FileService(self.temp_dir)
        
        # Create some test files
        filenames = ["file1.txt", "file2.txt", "file3.txt"]
        for filename in filenames:
            with open(os.path.join(self.temp_dir, filename), 'w') as f:
                f.write("test")
        
        # List files in directory
        listed_files = service.list_files()
        
        # Verify all created files are listed
        for filename in filenames:
            assert filename in listed_files
    
    def test_list_files_subdirectory(self):
        """Test listing files in a subdirectory"""
        service = FileService(self.temp_dir)
        
        # Create a subdirectory with files
        subdir = "subdir"
        os.makedirs(os.path.join(self.temp_dir, subdir))
        
        subdir_files = ["subfile1.txt", "subfile2.txt"]
        for filename in subdir_files:
            with open(os.path.join(self.temp_dir, subdir, filename), 'w') as f:
                f.write("test")
        
        # List files in subdirectory
        listed_files = service.list_files(subdir)
        
        # Verify all created files in subdirectory are listed
        assert len(listed_files) == len(subdir_files)
        for filename in subdir_files:
            assert filename in listed_files
    
    def test_list_files_nonexistent_directory(self):
        """Test listing files in a non-existent directory"""
        service = FileService(self.temp_dir)
        
        with pytest.raises(FileNotFoundError, match="Directory not found"):
            service.list_files("nonexistent_dir")
    
    def test_list_files_io_error(self):
        """Test directory listing failure handling"""
        service = FileService(self.temp_dir)
        
        # Mock os.listdir to raise IOError
        with patch('os.listdir', side_effect=IOError("IO Error")):
            with pytest.raises(ValueError, match="Failed to list directory"):
                service.list_files()
    
    def test_get_secure_path_normal(self):
        """Test _get_secure_path with normal relative path"""
        service = FileService(self.temp_dir)
        
        filename = "test.txt"
        secure_path = service._get_secure_path(filename)
        
        expected_path = os.path.join(self.temp_dir, filename)
        assert secure_path == expected_path
    
    def test_get_secure_path_with_directory(self):
        """Test _get_secure_path with subdirectory path"""
        service = FileService(self.temp_dir)
        
        path = "subdir/test.txt"
        secure_path = service._get_secure_path(path)
        
        expected_path = os.path.join(self.temp_dir, path)
        assert secure_path == expected_path
    
    def test_get_secure_path_with_traversal_attempt(self):
        """Test _get_secure_path handles directory traversal attempt"""
        service = FileService(self.temp_dir)
        
        # Attempt to go above base_dir using relative path
        path = "../../../etc/passwd"
        secure_path = service._get_secure_path(path)
        
        # Should sanitize to just the filename in the base directory
        expected_path = os.path.join(self.temp_dir, "passwd")
        assert secure_path == expected_path
        assert self.temp_dir in secure_path
        assert "../" not in secure_path
    
    def test_get_secure_path_rejects_absolute_paths(self):
        """Test _get_secure_path rejects absolute paths"""
        service = FileService(self.temp_dir)
        
        with pytest.raises(ValueError, match="Absolute paths not allowed"):
            service._get_secure_path("/absolute/path")
