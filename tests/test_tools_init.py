import pytest
from unittest.mock import Mock, AsyncMock
from tools import Tool


class TestTool:
    def test_tool_init_with_defaults(self):
        tool = Tool()
        assert tool.name is None
        assert tool.description is None
        assert tool.parameters == {}
        assert tool._session is None

    def test_tool_init_with_parameters(self):
        mock_session = Mock()
        tool = Tool(
            name="test_tool",
            description="A test tool",
            parameters={"type": "object"},
            session=mock_session
        )
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert tool.parameters == {"type": "object"}
        assert tool._session == mock_session

    def test_tool_properties(self):
        tool = Tool(
            name="example_tool",
            description="Example description",
            parameters={"key": "value"}
        )
        assert tool.name == "example_tool"
        assert tool.description == "Example description"
        assert tool.parameters == {"key": "value"}

    def test_tool_define_method(self):
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
    async def test_tool_run_without_session(self):
        tool = Tool(name="test_tool")
        result = await tool.run()
        assert result == {}

    @pytest.mark.asyncio
    async def test_tool_run_with_session_no_data(self):
        mock_session = AsyncMock()
        mock_session.call_tool.return_value = None
        
        tool = Tool(name="test_tool", session=mock_session)
        result = await tool.run(param1="value1")
        
        assert result == {}
        mock_session.call_tool.assert_called_once_with("test_tool", {"param1": "value1"})

    @pytest.mark.asyncio
    async def test_tool_run_with_session_empty_data(self):
        mock_session = AsyncMock()
        mock_session.call_tool.return_value = []
        
        tool = Tool(name="test_tool", session=mock_session)
        result = await tool.run(param1="value1")
        
        assert result == {}
        mock_session.call_tool.assert_called_once_with("test_tool", {"param1": "value1"})

    @pytest.mark.asyncio
    async def test_tool_run_with_session_valid_content(self):
        mock_session = AsyncMock()
        mock_session.call_tool.return_value = [
            ("content", {"result": "success"}),
            ("other", "ignored")
        ]
        
        tool = Tool(name="test_tool", session=mock_session)
        result = await tool.run(param1="value1")
        
        assert result == {"result": "success"}
        mock_session.call_tool.assert_called_once_with("test_tool", {"param1": "value1"})

    @pytest.mark.asyncio
    async def test_tool_run_with_session_no_content_type(self):
        mock_session = AsyncMock()
        mock_session.call_tool.return_value = [
            ("error", "some error"),
            ("metadata", {"info": "data"})
        ]
        
        tool = Tool(name="test_tool", session=mock_session)
        result = await tool.run(param1="value1")
        
        assert result == {}
        mock_session.call_tool.assert_called_once_with("test_tool", {"param1": "value1"})

    def test_tool_parameters_default_empty_dict(self):
        tool1 = Tool()
        tool2 = Tool()
        
        # Ensure default empty dict doesn't create shared mutable state
        tool1.parameters["new_key"] = "value"
        assert "new_key" not in tool2.parameters
