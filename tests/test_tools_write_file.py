import pytest
from unittest.mock import Mock, patch
from tools.write_file import WriteFile

class TestWriteFile:
    def test_write_file_properties(self):
        write_file = WriteFile()
        assert write_file.name == "write_file"
        assert write_file.description == "Write content to a specified file within a secure base directory."
        
        parameters = write_file.parameters
        assert parameters["type"] == "object"
        assert "base_dir" in parameters["properties"]
        assert "filename" in parameters["properties"]
        assert "content" in parameters["properties"]
        assert parameters["required"] == ["base_dir", "filename", "content"]

    def test_write_file_init_with_session(self):
        mock_session = Mock()
        write_file = WriteFile(session=mock_session)
        assert write_file._session == mock_session

    def test_write_file_define_method(self):
        write_file = WriteFile()
        definition = write_file.define()
        
        assert definition["type"] == "function"
        assert definition["function"]["name"] == "write_file"
        assert definition["function"]["description"] == "Write content to a specified file within a secure base directory."
        assert definition["function"]["parameters"]["type"] == "object"

    @pytest.mark.asyncio
    @patch('libs.fileops.file.FileService')
    async def test_write_file_run_success(self, mock_file_service):
        mock_service_instance = Mock()
        mock_file_service.return_value = mock_service_instance
        
        write_file = WriteFile()
        result = await write_file.run(
            base_dir="/test/dir", 
            filename="test.txt", 
            content="Hello, World!"
        )
        
        assert result["success"] is True
        assert result["filename"] == "test.txt"
        assert result["base_dir"] == "/test/dir"
        assert "Successfully wrote content" in result["result"]
        
        mock_file_service.assert_called_once_with("/test/dir")
        mock_service_instance.write_to_file.assert_called_once_with("test.txt", "Hello, World!")

    @pytest.mark.asyncio
    @patch('libs.fileops.file.FileService')
    async def test_write_file_run_permission_error(self, mock_file_service):
        mock_service_instance = Mock()
        mock_service_instance.write_to_file.side_effect = PermissionError("Permission denied")
        mock_file_service.return_value = mock_service_instance
        
        write_file = WriteFile()
        result = await write_file.run(
            base_dir="/test/dir", 
            filename="restricted.txt", 
            content="Some content"
        )
        
        assert result["success"] is False
        assert result["filename"] == "restricted.txt"
        assert result["base_dir"] == "/test/dir"
        assert "Failed to write to file" in result["result"]
        assert "Permission denied" in result["result"]

    @pytest.mark.asyncio
    @patch('libs.fileops.file.FileService')
    async def test_write_file_run_disk_full_error(self, mock_file_service):
        mock_service_instance = Mock()
        mock_service_instance.write_to_file.side_effect = OSError("No space left on device")
        mock_file_service.return_value = mock_service_instance
        
        write_file = WriteFile()
        result = await write_file.run(
            base_dir="/test/dir", 
            filename="large.txt", 
            content="Large content"
        )
        
        assert result["success"] is False
        assert "No space left on device" in result["result"]

    @pytest.mark.asyncio
    @patch('libs.fileops.file.FileService')
    async def test_write_file_run_empty_content(self, mock_file_service):
        mock_service_instance = Mock()
        mock_file_service.return_value = mock_service_instance
        
        write_file = WriteFile()
        result = await write_file.run(
            base_dir="/test/dir", 
            filename="empty.txt", 
            content=""
        )
        
        assert result["success"] is True
        assert result["filename"] == "empty.txt"
        mock_service_instance.write_to_file.assert_called_once_with("empty.txt", "")

    @pytest.mark.asyncio
    @patch('libs.fileops.file.FileService')
    async def test_write_file_run_unicode_content(self, mock_file_service):
        mock_service_instance = Mock()
        mock_file_service.return_value = mock_service_instance
        
        unicode_content = "Unicode content: 测试 🚀 émojis"
        write_file = WriteFile()
        result = await write_file.run(
            base_dir="/test/dir", 
            filename="unicode.txt", 
            content=unicode_content
        )
        
        assert result["success"] is True
        mock_service_instance.write_to_file.assert_called_once_with("unicode.txt", unicode_content)

    @pytest.mark.asyncio
    async def test_write_file_inheritance(self):
        from tools import Tool
        write_file = WriteFile()
        assert isinstance(write_file, Tool)

    def test_write_file_parameters_validation(self):
        write_file = WriteFile()
        params = write_file.parameters
        
        # Check base_dir parameter
        base_dir_prop = params["properties"]["base_dir"]
        assert base_dir_prop["type"] == "string"
        assert "Base directory" in base_dir_prop["description"]
        
        # Check filename parameter
        filename_prop = params["properties"]["filename"]
        assert filename_prop["type"] == "string"
        assert "relative path" in filename_prop["description"]
        
        # Check content parameter
        content_prop = params["properties"]["content"]
        assert content_prop["type"] == "string"
        assert "content to write" in content_prop["description"]

    @pytest.mark.asyncio
    @patch('libs.fileops.file.FileService')
    async def test_write_file_run_large_content(self, mock_file_service):
        mock_service_instance = Mock()
        mock_file_service.return_value = mock_service_instance
        
        large_content = "x" * 50000  # 50KB content
        write_file = WriteFile()
        result = await write_file.run(
            base_dir="/test/dir", 
            filename="large.txt", 
            content=large_content
        )
        
        assert result["success"] is True
        mock_service_instance.write_to_file.assert_called_once_with("large.txt", large_content)

    @pytest.mark.asyncio
    @patch('libs.fileops.file.FileService')
    async def test_write_file_run_path_traversal_protection(self, mock_file_service):
        mock_service_instance = Mock()
        mock_service_instance.write_to_file.side_effect = ValueError("Path traversal detected")
        mock_file_service.return_value = mock_service_instance
        
        write_file = WriteFile()
        result = await write_file.run(
            base_dir="/test/dir", 
            filename="../../../etc/passwd", 
            content="malicious content"
        )
        
        assert result["success"] is False
        assert "Path traversal detected" in result["result"]

    @pytest.mark.asyncio
    @patch('libs.fileops.file.FileService')
    async def test_write_file_run_multiline_content(self, mock_file_service):
        mock_service_instance = Mock()
        mock_file_service.return_value = mock_service_instance
        
        multiline_content = "Line 1\nLine 2\nLine 3\n"
        write_file = WriteFile()
        result = await write_file.run(
            base_dir="/test/dir", 
            filename="multiline.txt", 
            content=multiline_content
        )
        
        assert result["success"] is True
        mock_service_instance.write_to_file.assert_called_once_with("multiline.txt", multiline_content)

    @pytest.mark.asyncio
    @patch('libs.fileops.file.FileService')
    async def test_write_file_run_json_content(self, mock_file_service):
        mock_service_instance = Mock()
        mock_file_service.return_value = mock_service_instance
        
        json_content = '{"key": "value", "number": 42, "array": [1, 2, 3]}'
        write_file = WriteFile()
        result = await write_file.run(
            base_dir="/test/dir", 
            filename="data.json", 
            content=json_content
        )
        
        assert result["success"] is True
        mock_service_instance.write_to_file.assert_called_once_with("data.json", json_content)
