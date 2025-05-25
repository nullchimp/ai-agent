import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.tools.read_file import ReadFile


class TestReadFile:
    def test_read_file_properties(self):
        read_file = ReadFile()
        assert read_file.name == "read_file"
        assert read_file.description == "Read content from a specified file within a secure base directory."
        
        parameters = read_file.parameters
        assert parameters["type"] == "object"
        assert "base_dir" in parameters["properties"]
        assert "filename" in parameters["properties"]
        assert parameters["required"] == ["base_dir", "filename"]

    def test_read_file_init_with_session(self):
        mock_session = Mock()
        read_file = ReadFile(session=mock_session)
        assert read_file._session == mock_session

    def test_read_file_define_method(self):
        read_file = ReadFile()
        definition = read_file.define()
        
        assert definition["type"] == "function"
        assert definition["function"]["name"] == "read_file"
        assert definition["function"]["description"] == "Read content from a specified file within a secure base directory."
        assert definition["function"]["parameters"]["type"] == "object"

    @pytest.mark.asyncio
    @patch('libs.fileops.file.FileService')
    async def test_read_file_run_success(self, mock_file_service):
        mock_service_instance = Mock()
        mock_service_instance.read_file.return_value = "File content here"
        mock_file_service.return_value = mock_service_instance
        
        read_file = ReadFile()
        result = await read_file.run(base_dir="/test/dir", filename="test.txt")
        
        assert result["success"] is True
        assert result["content"] == "File content here"
        assert result["filename"] == "test.txt"
        assert result["base_dir"] == "/test/dir"
        assert "Successfully read content" in result["result"]
        
        mock_file_service.assert_called_once_with("/test/dir")
        mock_service_instance.read_file.assert_called_once_with("test.txt")

    @pytest.mark.asyncio
    @patch('libs.fileops.file.FileService')
    async def test_read_file_run_file_not_found(self, mock_file_service):
        mock_service_instance = Mock()
        mock_service_instance.read_file.side_effect = FileNotFoundError("File not found")
        mock_file_service.return_value = mock_service_instance
        
        read_file = ReadFile()
        result = await read_file.run(base_dir="/test/dir", filename="missing.txt")
        
        assert result["success"] is False
        assert result["content"] is None
        assert result["filename"] == "missing.txt"
        assert result["base_dir"] == "/test/dir"
        assert "Failed to read file" in result["result"]
        assert "File not found" in result["result"]

    @pytest.mark.asyncio
    @patch('libs.fileops.file.FileService')
    async def test_read_file_run_permission_error(self, mock_file_service):
        mock_service_instance = Mock()
        mock_service_instance.read_file.side_effect = PermissionError("Permission denied")
        mock_file_service.return_value = mock_service_instance
        
        read_file = ReadFile()
        result = await read_file.run(base_dir="/test/dir", filename="restricted.txt")
        
        assert result["success"] is False
        assert result["content"] is None
        assert "Permission denied" in result["result"]

    @pytest.mark.asyncio
    @patch('libs.fileops.file.FileService')
    async def test_read_file_run_empty_file(self, mock_file_service):
        mock_service_instance = Mock()
        mock_service_instance.read_file.return_value = ""
        mock_file_service.return_value = mock_service_instance
        
        read_file = ReadFile()
        result = await read_file.run(base_dir="/test/dir", filename="empty.txt")
        
        assert result["success"] is True
        assert result["content"] == ""
        assert result["filename"] == "empty.txt"

    @pytest.mark.asyncio
    @patch('libs.fileops.file.FileService')
    async def test_read_file_run_unicode_content(self, mock_file_service):
        unicode_content = "Unicode content: 测试 🚀 émojis"
        mock_service_instance = Mock()
        mock_service_instance.read_file.return_value = unicode_content
        mock_file_service.return_value = mock_service_instance
        
        read_file = ReadFile()
        result = await read_file.run(base_dir="/test/dir", filename="unicode.txt")
        
        assert result["success"] is True
        assert result["content"] == unicode_content

    @pytest.mark.asyncio
    async def test_read_file_inheritance(self):
        from src.tools import Tool
        read_file = ReadFile()
        assert isinstance(read_file, Tool)

    def test_read_file_parameters_validation(self):
        read_file = ReadFile()
        params = read_file.parameters
        
        # Check base_dir parameter
        base_dir_prop = params["properties"]["base_dir"]
        assert base_dir_prop["type"] == "string"
        assert "Base directory" in base_dir_prop["description"]
        
        # Check filename parameter
        filename_prop = params["properties"]["filename"]
        assert filename_prop["type"] == "string"
        assert "relative path" in filename_prop["description"]

    @pytest.mark.asyncio
    @patch('libs.fileops.file.FileService')
    async def test_read_file_run_large_file(self, mock_file_service):
        large_content = "x" * 10000  # 10KB content
        mock_service_instance = Mock()
        mock_service_instance.read_file.return_value = large_content
        mock_file_service.return_value = mock_service_instance
        
        read_file = ReadFile()
        result = await read_file.run(base_dir="/test/dir", filename="large.txt")
        
        assert result["success"] is True
        assert len(result["content"]) == 10000
        assert result["content"] == large_content

    @pytest.mark.asyncio
    @patch('libs.fileops.file.FileService')
    async def test_read_file_run_path_traversal_protection(self, mock_file_service):
        mock_service_instance = Mock()
        mock_service_instance.read_file.side_effect = ValueError("Path traversal detected")
        mock_file_service.return_value = mock_service_instance
        
        read_file = ReadFile()
        result = await read_file.run(base_dir="/test/dir", filename="../../../etc/passwd")
        
        assert result["success"] is False
        assert "Path traversal detected" in result["result"]
