import pytest
import os
import tempfile
from unittest.mock import patch, mock_open, MagicMock

from libs.fileops.file import FileService


class TestFileService:
    
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def file_service(self, temp_dir):
        return FileService(temp_dir)
    
    def test_init_creates_directory_if_not_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = os.path.join(tmpdir, "new_dir")
            service = FileService(new_dir)
            assert os.path.exists(new_dir)
            assert service.base_dir == os.path.abspath(new_dir)
    
    def test_init_with_existing_directory(self, temp_dir):
        service = FileService(temp_dir)
        assert service.base_dir == os.path.abspath(temp_dir)
    
    def test_init_fails_with_invalid_path(self):
        with patch("os.makedirs", side_effect=OSError("Permission denied")):
            with pytest.raises(ValueError, match="Failed to create base directory"):
                FileService("/invalid/path")
    
    def test_write_to_file_success(self, file_service, temp_dir):
        content = "test content"
        filename = "test.txt"
        
        file_service.write_to_file(filename, content)
        
        with open(os.path.join(temp_dir, filename), 'r') as f:
            assert f.read() == content
    
    def test_write_to_file_creates_subdirectory(self, file_service, temp_dir):
        content = "test content"
        filename = "subdir/test.txt"
        
        file_service.write_to_file(filename, content)
        
        assert os.path.exists(os.path.join(temp_dir, "subdir"))
        with open(os.path.join(temp_dir, "subdir", "test.txt"), 'r') as f:
            assert f.read() == content
    
    def test_write_to_file_fails_with_io_error(self, file_service):
        with patch("builtins.open", side_effect=IOError("Permission denied")):
            with pytest.raises(ValueError, match="Failed to write file"):
                file_service.write_to_file("test.txt", "content")
    
    def test_read_file_success(self, file_service, temp_dir):
        filename = "test.txt"
        content = "test content"
        
        with open(os.path.join(temp_dir, filename), 'w') as f:
            f.write(content)
        
        result = file_service.read_file(filename)
        assert result == content
    
    def test_read_file_not_found(self, file_service):
        with pytest.raises(FileNotFoundError, match="File not found: nonexistent.txt"):
            file_service.read_file("nonexistent.txt")
    
    def test_read_file_fails_with_io_error(self, file_service, temp_dir):
        filename = "test.txt"
        
        # Create file first
        with open(os.path.join(temp_dir, filename), 'w') as f:
            f.write("content")
        
        with patch("builtins.open", side_effect=IOError("Permission denied")):
            with pytest.raises(ValueError, match="Failed to read file"):
                file_service.read_file(filename)
    
    def test_list_files_success(self, file_service, temp_dir):
        # Create test files
        files = ["file1.txt", "file2.txt", "file3.py"]
        for filename in files:
            with open(os.path.join(temp_dir, filename), 'w') as f:
                f.write("content")
        
        result = file_service.list_files(".")
        assert set(result) == set(files)
    
    def test_list_files_subdirectory(self, file_service, temp_dir):
        # Create subdirectory with files
        subdir = "subdir"
        os.makedirs(os.path.join(temp_dir, subdir))
        files = ["sub1.txt", "sub2.txt"]
        for filename in files:
            with open(os.path.join(temp_dir, subdir, filename), 'w') as f:
                f.write("content")
        
        result = file_service.list_files(subdir)
        assert set(result) == set(files)
    
    def test_list_files_directory_not_found(self, file_service):
        with pytest.raises(FileNotFoundError, match="Directory not found: nonexistent"):
            file_service.list_files("nonexistent")
    
    def test_list_files_fails_with_io_error(self, file_service, temp_dir):
        with patch("os.listdir", side_effect=IOError("Permission denied")):
            with pytest.raises(ValueError, match="Failed to list directory"):
                file_service.list_files(".")
    
    def test_get_secure_path_relative_path(self, file_service, temp_dir):
        result = file_service._get_secure_path("test.txt")
        expected = os.path.join(temp_dir, "test.txt")
        assert result == expected
    
    def test_get_secure_path_absolute_path_raises_error(self, file_service):
        with pytest.raises(ValueError, match="Absolute paths not allowed"):
            file_service._get_secure_path("/absolute/path/test.txt")
    
    def test_get_secure_path_path_traversal_protection(self, file_service, temp_dir):
        result = file_service._get_secure_path("../../../etc/passwd")
        expected = os.path.join(temp_dir, "passwd")
        assert result == expected
    
    def test_get_secure_path_normalizes_path(self, file_service, temp_dir):
        result = file_service._get_secure_path("./subdir/../test.txt")
        expected = os.path.join(temp_dir, "test.txt")
        assert result == expected
