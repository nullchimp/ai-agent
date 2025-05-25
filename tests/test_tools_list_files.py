import pytest
from unittest.mock import Mock, patch
from src.tools.list_files import ListFiles


class TestListFiles:
    def test_list_files_properties(self):
        list_files = ListFiles()
        assert list_files.name == "list_files"
        assert list_files.description == "List files in a specified directory within a secure base directory."
        
        parameters = list_files.parameters
        assert parameters["type"] == "object"
        assert "base_dir" in parameters["properties"]
        assert "directory" in parameters["properties"]
        assert parameters["required"] == ["base_dir"]

    def test_list_files_init_with_session(self):
        mock_session = Mock()
        list_files = ListFiles(session=mock_session)
        assert list_files._session == mock_session

    def test_list_files_define_method(self):
        list_files = ListFiles()
        definition = list_files.define()
        
        assert definition["type"] == "function"
        assert definition["function"]["name"] == "list_files"
        assert definition["function"]["description"] == "List files in a specified directory within a secure base directory."
        assert definition["function"]["parameters"]["type"] == "object"

    @pytest.mark.asyncio
    @patch('libs.fileops.file.FileService')
    async def test_list_files_run_success_default_directory(self, mock_file_service):
        mock_service_instance = Mock()
        mock_service_instance.list_files.return_value = ["file1.txt", "file2.py", "dir1/"]
        mock_file_service.return_value = mock_service_instance
        
        list_files = ListFiles()
        result = await list_files.run(base_dir="/test/dir")
        
        assert result["success"] is True
        assert result["base_dir"] == "/test/dir"
        assert result["directory"] == "."
        assert result["files"] == ["file1.txt", "file2.py", "dir1/"]
        assert "Successfully listed files" in result["result"]
        
        mock_file_service.assert_called_once_with("/test/dir")
        mock_service_instance.list_files.assert_called_once_with(".")

    @pytest.mark.asyncio
    @patch('libs.fileops.file.FileService')
    async def test_list_files_run_success_specific_directory(self, mock_file_service):
        mock_service_instance = Mock()
        mock_service_instance.list_files.return_value = ["subfile1.txt", "subfile2.json"]
        mock_file_service.return_value = mock_service_instance
        
        list_files = ListFiles()
        result = await list_files.run(base_dir="/test/dir", directory="subdir")
        
        assert result["success"] is True
        assert result["base_dir"] == "/test/dir"
        assert result["directory"] == "subdir"
        assert result["files"] == ["subfile1.txt", "subfile2.json"]
        
        mock_service_instance.list_files.assert_called_once_with("subdir")

    @pytest.mark.asyncio
    @patch('libs.fileops.file.FileService')
    async def test_list_files_run_empty_directory(self, mock_file_service):
        mock_service_instance = Mock()
        mock_service_instance.list_files.return_value = []
        mock_file_service.return_value = mock_service_instance
        
        list_files = ListFiles()
        result = await list_files.run(base_dir="/test/dir", directory="empty")
        
        assert result["success"] is True
        assert result["files"] == []
        assert result["directory"] == "empty"

    @pytest.mark.asyncio
    @patch('libs.fileops.file.FileService')
    async def test_list_files_run_directory_not_found(self, mock_file_service):
        mock_service_instance = Mock()
        mock_service_instance.list_files.side_effect = FileNotFoundError("Directory not found")
        mock_file_service.return_value = mock_service_instance
        
        list_files = ListFiles()
        result = await list_files.run(base_dir="/test/dir", directory="missing")
        
        assert result["success"] is False
        assert result["files"] == []
        assert result["directory"] == "missing"
        assert "Failed to list files" in result["result"]
        assert "Directory not found" in result["result"]

    @pytest.mark.asyncio
    @patch('libs.fileops.file.FileService')
    async def test_list_files_run_permission_error(self, mock_file_service):
        mock_service_instance = Mock()
        mock_service_instance.list_files.side_effect = PermissionError("Permission denied")
        mock_file_service.return_value = mock_service_instance
        
        list_files = ListFiles()
        result = await list_files.run(base_dir="/test/dir", directory="restricted")
        
        assert result["success"] is False
        assert result["files"] == []
        assert "Permission denied" in result["result"]

    @pytest.mark.asyncio
    async def test_list_files_inheritance(self):
        from src.tools import Tool
        list_files = ListFiles()
        assert isinstance(list_files, Tool)

    def test_list_files_parameters_validation(self):
        list_files = ListFiles()
        params = list_files.parameters
        
        # Check base_dir parameter
        base_dir_prop = params["properties"]["base_dir"]
        assert base_dir_prop["type"] == "string"
        assert "Base directory" in base_dir_prop["description"]
        
        # Check directory parameter
        directory_prop = params["properties"]["directory"]
        assert directory_prop["type"] == "string"
        assert "relative subdirectory" in directory_prop["description"]
        assert "default: '.'" in directory_prop["description"]

    @pytest.mark.asyncio
    @patch('libs.fileops.file.FileService')
    async def test_list_files_run_nested_directory(self, mock_file_service):
        mock_service_instance = Mock()
        mock_service_instance.list_files.return_value = ["nested1.txt", "nested2.py", "deepdir/"]
        mock_file_service.return_value = mock_service_instance
        
        list_files = ListFiles()
        result = await list_files.run(base_dir="/test/dir", directory="level1/level2")
        
        assert result["success"] is True
        assert result["directory"] == "level1/level2"
        assert result["files"] == ["nested1.txt", "nested2.py", "deepdir/"]
        
        mock_service_instance.list_files.assert_called_once_with("level1/level2")

    @pytest.mark.asyncio
    @patch('libs.fileops.file.FileService')
    async def test_list_files_run_with_various_file_types(self, mock_file_service):
        mock_service_instance = Mock()
        file_list = [
            "document.txt", "script.py", "data.json", "image.png",
            "archive.zip", "config.yaml", "style.css", "subdirectory/"
        ]
        mock_service_instance.list_files.return_value = file_list
        mock_file_service.return_value = mock_service_instance
        
        list_files = ListFiles()
        result = await list_files.run(base_dir="/test/dir", directory="mixed")
        
        assert result["success"] is True
        assert result["files"] == file_list
        assert len(result["files"]) == 8

    @pytest.mark.asyncio
    @patch('libs.fileops.file.FileService')
    async def test_list_files_run_path_traversal_protection(self, mock_file_service):
        mock_service_instance = Mock()
        mock_service_instance.list_files.side_effect = ValueError("Path traversal detected")
        mock_file_service.return_value = mock_service_instance
        
        list_files = ListFiles()
        result = await list_files.run(base_dir="/test/dir", directory="../../../etc")
        
        assert result["success"] is False
        assert "Path traversal detected" in result["result"]

    @pytest.mark.asyncio
    @patch('libs.fileops.file.FileService')
    async def test_list_files_run_large_directory(self, mock_file_service):
        mock_service_instance = Mock()
        # Simulate a directory with many files
        large_file_list = [f"file_{i:04d}.txt" for i in range(1000)]
        mock_service_instance.list_files.return_value = large_file_list
        mock_file_service.return_value = mock_service_instance
        
        list_files = ListFiles()
        result = await list_files.run(base_dir="/test/dir", directory="large")
        
        assert result["success"] is True
        assert len(result["files"]) == 1000
        assert "file_0000.txt" in result["files"]
        assert "file_0999.txt" in result["files"]
