import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio

from tools import Tool
from tools.google_search import GoogleSearch
from tools.read_file import ReadFile
from tools.write_file import WriteFile
from tools.list_files import ListFiles


class TestTool:

    def test_tool_initialization_with_defaults(self):
        tool = Tool()
        assert tool.name is None
        assert tool.description is None
        assert tool.parameters == {}
        assert tool._session is None

    def test_tool_initialization_with_values(self):
        mock_session = Mock()
        tool = Tool(
            name="test_tool",
            description="Test description",
            parameters={"param1": "value1"},
            session=mock_session
        )
        
        assert tool.name == "test_tool"
        assert tool.description == "Test description"
        assert tool.parameters == {"param1": "value1"}
        assert tool._session == mock_session

    def test_define_method(self):
        tool = Tool(
            name="test_tool",
            description="Test description",
            parameters={"type": "object", "properties": {}}
        )
        
        definition = tool.define()
        expected = {
            "type": "function",
            "function": {
                "name": "test_tool",
                "description": "Test description",
                "parameters": {"type": "object", "properties": {}}
            }
        }
        
        assert definition == expected

    @pytest.mark.asyncio
    async def test_run_without_session(self):
        tool = Tool()
        result = await tool.run()
        assert result == {}

    @pytest.mark.asyncio
    async def test_run_with_session_no_data(self):
        mock_session = AsyncMock()
        mock_session.call_tool.return_value = None
        
        tool = Tool(name="test_tool", session=mock_session)
        result = await tool.run(arg1="value1")
        
        assert result == {}
        mock_session.call_tool.assert_called_once_with("test_tool", {"arg1": "value1"})

    @pytest.mark.asyncio
    async def test_run_with_session_with_data(self):
        mock_session = AsyncMock()
        mock_session.call_tool.return_value = [
            ("content", {"result": "success"}),
            ("other", "ignore")
        ]
        
        tool = Tool(name="test_tool", session=mock_session)
        result = await tool.run(arg1="value1")
        
        assert result == {"result": "success"}
        mock_session.call_tool.assert_called_once_with("test_tool", {"arg1": "value1"})


class TestGoogleSearch:

    def test_google_search_properties(self):
        tool = GoogleSearch()
        
        assert tool.name == "google_search"
        assert "Search the web" in tool.description
        
        params = tool.parameters
        assert params["type"] == "object"
        assert "query" in params["properties"]
        assert "num_results" in params["properties"]
        assert params["required"] == ["query"]

    @patch('libs.search.service.Service')
    @pytest.mark.asyncio
    async def test_google_search_run(self, mock_service_class):
        mock_service = Mock()
        mock_results = Mock()
        mock_results.query = "test query"
        mock_results.total_results = 5
        mock_results.search_time = 0.123
        mock_results.results = [Mock()]
        mock_results.formatted_count = "5"
        
        mock_service.search.return_value = mock_results
        mock_service_class.create.return_value = mock_service
        
        tool = GoogleSearch()
        result = await tool.run("test query", 5)
        
        assert result["query"] == "test query"
        assert result["total_results"] == 5
        assert result["search_time"] == 0.123
        assert result["formatted_count"] == "5"
        assert len(result["results"]) == 1
        
        mock_service_class.create.assert_called_once()
        mock_service.search.assert_called_once_with("test query", 5)

    @patch('libs.search.service.Service')
    @pytest.mark.asyncio
    async def test_google_search_run_default_results(self, mock_service_class):
        mock_service = Mock()
        mock_results = Mock()
        mock_results.query = "test query"
        mock_results.total_results = 5
        mock_results.search_time = 0.123
        mock_results.results = []
        mock_results.formatted_count = "5"
        
        mock_service.search.return_value = mock_results
        mock_service_class.create.return_value = mock_service
        
        tool = GoogleSearch()
        result = await tool.run("test query")
        
        mock_service.search.assert_called_once_with("test query", 5)


class TestReadFile:

    def test_read_file_properties(self):
        tool = ReadFile()
        
        assert tool.name == "read_file"
        assert "Read content from" in tool.description
        
        params = tool.parameters
        assert params["type"] == "object"
        assert "base_dir" in params["properties"]
        assert "filename" in params["properties"]
        assert params["required"] == ["base_dir", "filename"]

    @patch('libs.fileops.file.FileService')
    @pytest.mark.asyncio
    async def test_read_file_success(self, mock_file_service_class):
        mock_service = Mock()
        mock_service.read_file.return_value = "file content"
        mock_file_service_class.return_value = mock_service
        
        tool = ReadFile()
        result = await tool.run("/base/dir", "test.txt")
        
        assert result["success"] is True
        assert result["content"] == "file content"
        assert result["filename"] == "test.txt"
        assert result["base_dir"] == "/base/dir"
        assert "Successfully read content" in result["result"]
        
        mock_file_service_class.assert_called_once_with("/base/dir")
        mock_service.read_file.assert_called_once_with("test.txt")

    @patch('libs.fileops.file.FileService')
    @pytest.mark.asyncio
    async def test_read_file_failure(self, mock_file_service_class):
        mock_service = Mock()
        mock_service.read_file.side_effect = FileNotFoundError("File not found")
        mock_file_service_class.return_value = mock_service
        
        tool = ReadFile()
        result = await tool.run("/base/dir", "nonexistent.txt")
        
        assert result["success"] is False
        assert result["content"] is None
        assert result["filename"] == "nonexistent.txt"
        assert result["base_dir"] == "/base/dir"
        assert "Failed to read file" in result["result"]
        
        mock_file_service_class.assert_called_once_with("/base/dir")
        mock_service.read_file.assert_called_once_with("nonexistent.txt")


class TestWriteFile:

    def test_write_file_properties(self):
        tool = WriteFile()
        
        assert tool.name == "write_file"
        assert "Write content to" in tool.description
        
        params = tool.parameters
        assert params["type"] == "object"
        assert "base_dir" in params["properties"]
        assert "filename" in params["properties"]
        assert "content" in params["properties"]
        assert params["required"] == ["base_dir", "filename", "content"]

    @patch('libs.fileops.file.FileService')
    @pytest.mark.asyncio
    async def test_write_file_success(self, mock_file_service_class):
        mock_service = Mock()
        mock_file_service_class.return_value = mock_service
        
        tool = WriteFile()
        result = await tool.run("/base/dir", "test.txt", "file content")
        
        assert result["success"] is True
        assert result["filename"] == "test.txt"
        assert result["base_dir"] == "/base/dir"
        assert "Successfully wrote content" in result["result"]
        
        mock_file_service_class.assert_called_once_with("/base/dir")
        mock_service.write_to_file.assert_called_once_with("test.txt", "file content")

    @patch('libs.fileops.file.FileService')
    @pytest.mark.asyncio
    async def test_write_file_failure(self, mock_file_service_class):
        mock_service = Mock()
        mock_service.write_to_file.side_effect = ValueError("Write failed")
        mock_file_service_class.return_value = mock_service
        
        tool = WriteFile()
        result = await tool.run("/base/dir", "test.txt", "content")
        
        assert result["success"] is False
        assert result["filename"] == "test.txt"
        assert result["base_dir"] == "/base/dir"
        assert "Failed to write to file" in result["result"]
        
        mock_file_service_class.assert_called_once_with("/base/dir")
        mock_service.write_to_file.assert_called_once_with("test.txt", "content")


class TestListFiles:

    def test_list_files_properties(self):
        tool = ListFiles()
        
        assert tool.name == "list_files"
        assert "List files in" in tool.description
        
        params = tool.parameters
        assert params["type"] == "object"
        assert "base_dir" in params["properties"]
        assert "directory" in params["properties"]
        assert params["required"] == ["base_dir"]

    @patch('libs.fileops.file.FileService')
    @pytest.mark.asyncio
    async def test_list_files_success(self, mock_file_service_class):
        mock_service = Mock()
        mock_service.list_files.return_value = ["file1.txt", "file2.txt"]
        mock_file_service_class.return_value = mock_service
        
        tool = ListFiles()
        result = await tool.run("/base/dir", "subdir")
        
        assert result["success"] is True
        assert result["files"] == ["file1.txt", "file2.txt"]
        assert result["directory"] == "subdir"
        assert result["base_dir"] == "/base/dir"
        assert "Successfully listed files" in result["result"]
        
        mock_file_service_class.assert_called_once_with("/base/dir")
        mock_service.list_files.assert_called_once_with("subdir")

    @patch('libs.fileops.file.FileService')
    @pytest.mark.asyncio
    async def test_list_files_default_directory(self, mock_file_service_class):
        mock_service = Mock()
        mock_service.list_files.return_value = ["file1.txt"]
        mock_file_service_class.return_value = mock_service
        
        tool = ListFiles()
        result = await tool.run("/base/dir")
        
        assert result["success"] is True
        assert result["directory"] == "."
        
        mock_service.list_files.assert_called_once_with(".")

    @patch('libs.fileops.file.FileService')
    @pytest.mark.asyncio
    async def test_list_files_failure(self, mock_file_service_class):
        mock_service = Mock()
        mock_service.list_files.side_effect = FileNotFoundError("Directory not found")
        mock_file_service_class.return_value = mock_service
        
        tool = ListFiles()
        result = await tool.run("/base/dir", "nonexistent")
        
        assert result["success"] is False
        assert result["files"] == []
        assert result["directory"] == "nonexistent"
        assert result["base_dir"] == "/base/dir"
        assert "Failed to list files" in result["result"]
        
        mock_file_service_class.assert_called_once_with("/base/dir")
        mock_service.list_files.assert_called_once_with("nonexistent")
