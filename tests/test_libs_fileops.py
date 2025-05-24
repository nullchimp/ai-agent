import pytest
from unittest.mock import Mock, patch, MagicMock
import os
import tempfile
import shutil

from libs.fileops.file import FileService


class TestFileService:

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.file_service = FileService(self.temp_dir)

    def teardown_method(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_init_existing_directory(self):
        service = FileService(self.temp_dir)
        assert service.base_dir == os.path.abspath(self.temp_dir)

    def test_init_nonexistent_directory(self):
        new_dir = os.path.join(self.temp_dir, "new_dir")
        service = FileService(new_dir)
        assert os.path.exists(new_dir)
        assert service.base_dir == os.path.abspath(new_dir)

    def test_init_permission_error(self):
        with patch('os.makedirs', side_effect=PermissionError("Permission denied")):
            with pytest.raises(ValueError, match="Failed to create base directory"):
                FileService("/nonexistent/path")

    def test_write_to_file_success(self):
        filename = "test.txt"
        content = "Hello, World!"
        
        self.file_service.write_to_file(filename, content)
        
        file_path = os.path.join(self.temp_dir, filename)
        assert os.path.exists(file_path)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            assert f.read() == content

    def test_write_to_file_with_subdirectory(self):
        filename = "subdir/test.txt"
        content = "Hello, World!"
        
        self.file_service.write_to_file(filename, content)
        
        file_path = os.path.join(self.temp_dir, filename)
        assert os.path.exists(file_path)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            assert f.read() == content

    def test_write_to_file_io_error(self):
        with patch('builtins.open', side_effect=IOError("Write failed")):
            with pytest.raises(ValueError, match="Failed to write file"):
                self.file_service.write_to_file("test.txt", "content")

    def test_read_file_success(self):
        filename = "test.txt"
        content = "Hello, World!"
        
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        result = self.file_service.read_file(filename)
        assert result == content

    def test_read_file_not_found(self):
        with pytest.raises(FileNotFoundError, match="File not found"):
            self.file_service.read_file("nonexistent.txt")

    def test_read_file_io_error(self):
        filename = "test.txt"
        file_path = os.path.join(self.temp_dir, filename)
        
        # Create file first
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("content")
        
        with patch('builtins.open', side_effect=IOError("Read failed")):
            with pytest.raises(ValueError, match="Failed to read file"):
                self.file_service.read_file(filename)

    def test_list_files_success(self):
        # Create test files
        test_files = ["file1.txt", "file2.py", "file3.md"]
        for filename in test_files:
            file_path = os.path.join(self.temp_dir, filename)
            with open(file_path, 'w') as f:
                f.write("test")
        
        result = self.file_service.list_files()
        for filename in test_files:
            assert filename in result

    def test_list_files_subdirectory(self):
        # Create subdirectory with files
        subdir = os.path.join(self.temp_dir, "subdir")
        os.makedirs(subdir)
        
        test_files = ["sub1.txt", "sub2.py"]
        for filename in test_files:
            file_path = os.path.join(subdir, filename)
            with open(file_path, 'w') as f:
                f.write("test")
        
        result = self.file_service.list_files("subdir")
        for filename in test_files:
            assert filename in result

    def test_list_files_directory_not_found(self):
        with pytest.raises(FileNotFoundError, match="Directory not found"):
            self.file_service.list_files("nonexistent")

    def test_list_files_io_error(self):
        with patch('os.listdir', side_effect=IOError("List failed")):
            with pytest.raises(ValueError, match="Failed to list directory"):
                self.file_service.list_files()

    def test_get_secure_path_relative(self):
        result = self.file_service._get_secure_path("test.txt")
        expected = os.path.join(self.temp_dir, "test.txt")
        assert result == expected

    def test_get_secure_path_absolute_rejected(self):
        with pytest.raises(ValueError, match="Absolute paths not allowed"):
            self.file_service._get_secure_path("/absolute/path")

    def test_get_secure_path_traversal_attack(self):
        # Test path traversal attack protection
        result = self.file_service._get_secure_path("../../../etc/passwd")
        # Should be sanitized to just the filename in base_dir
        expected = os.path.join(self.temp_dir, "passwd")
        assert result == expected

    def test_get_secure_path_subdirectory_traversal(self):
        # Test legitimate subdirectory access
        result = self.file_service._get_secure_path("subdir/file.txt")
        expected = os.path.join(self.temp_dir, "subdir/file.txt")
        assert result == expected

    def test_get_secure_path_normalize(self):
        # Test path normalization
        result = self.file_service._get_secure_path("./subdir/../file.txt")
        expected = os.path.join(self.temp_dir, "file.txt")
        assert result == expected
