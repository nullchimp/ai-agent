import os
import tempfile
import shutil
import pytest
from libs.fileops.file import FileService


def test_write_and_read_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        service = FileService(tmpdir)
        filename = "test.txt"
        content = "Hello, world!"
        service.write_to_file(filename, content)
        read_content = service.read_file(filename)
        assert read_content == content


def test_list_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        service = FileService(tmpdir)
        filenames = ["a.txt", "b.txt"]
        for fname in filenames:
            service.write_to_file(fname, "data")
        files = service.list_files()
        assert set(files) >= set(filenames)


def test_read_file_not_found():
    with tempfile.TemporaryDirectory() as tmpdir:
        service = FileService(tmpdir)
        with pytest.raises(FileNotFoundError):
            service.read_file("doesnotexist.txt")


def test_list_files_directory_not_found():
    with tempfile.TemporaryDirectory() as tmpdir:
        service = FileService(tmpdir)
        with pytest.raises(FileNotFoundError):
            service.list_files("notadir")


def test_write_to_file_absolute_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        service = FileService(tmpdir)
        with pytest.raises(ValueError):
            service.write_to_file("/etc/passwd", "bad")


def test_secure_path_traversal():
    with tempfile.TemporaryDirectory() as tmpdir:
        service = FileService(tmpdir)
        # Should not allow escaping base_dir
        service.write_to_file("../escape.txt", "safe")
        # File should be created in base_dir, not above
        files = service.list_files()
        assert "escape.txt" in files
