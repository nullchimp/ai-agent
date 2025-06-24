import pytest
from unittest.mock import Mock, patch, AsyncMock
from agent import Agent, get_agent_instance, delete_agent_instance, _agent_sessions


class TestAgentSessionManagement:
    def setup_method(self):
        # Clear sessions before each test
        _agent_sessions.clear()

    def teardown_method(self):
        # Clear sessions after each test
        _agent_sessions.clear()

    @pytest.mark.asyncio
    @patch("src.agent.Chat.create")
    @patch("agent.Agent.initialize_mcp_tools", new_callable=AsyncMock)
    async def test_get_agent_instance_creates_new_session(self, mock_initialize_mcp, mock_chat_create):
        mock_chat = Mock()
        mock_chat.tools = []
        mock_chat_create.return_value = mock_chat

        session_id = "test-session-1"
        agent = await get_agent_instance(session_id)

        assert isinstance(agent, Agent)
        assert agent.session_id == session_id
        assert session_id in _agent_sessions
        assert _agent_sessions[session_id] is agent

    @pytest.mark.asyncio
    @patch("src.agent.Chat.create")
    @patch("agent.Agent.initialize_mcp_tools", new_callable=AsyncMock)
    async def test_get_agent_instance_returns_existing_session(self, mock_initialize_mcp, mock_chat_create):
        mock_chat = Mock()
        mock_chat.tools = []
        mock_chat_create.return_value = mock_chat

        session_id = "test-session-2"
        
        # First call creates the agent
        agent1 = await get_agent_instance(session_id)
        
        # Second call returns the same agent
        agent2 = await get_agent_instance(session_id)
        
        assert agent1 is agent2
        assert len(_agent_sessions) == 1

    @pytest.mark.asyncio
    @patch("src.agent.Chat.create")
    @patch("agent.Agent.initialize_mcp_tools", new_callable=AsyncMock)
    async def test_multiple_sessions_stored_separately(self, mock_initialize_mcp, mock_chat_create):
        mock_chat = Mock()
        mock_chat.tools = []
        mock_chat_create.return_value = mock_chat

        session1 = "test-session-1"
        session2 = "test-session-2"
        
        agent1 = await get_agent_instance(session1)
        agent2 = await get_agent_instance(session2)
        
        assert agent1 is not agent2
        assert agent1.session_id == session1
        assert agent2.session_id == session2
        assert len(_agent_sessions) == 2
        assert _agent_sessions[session1] is agent1
        assert _agent_sessions[session2] is agent2

    @pytest.mark.asyncio
    @patch("src.agent.Chat.create")
    @patch("agent.Agent.initialize_mcp_tools", new_callable=AsyncMock)
    async def test_delete_agent_instance_removes_session(self, mock_initialize_mcp, mock_chat_create):
        mock_chat = Mock()
        mock_chat.tools = []
        mock_chat_create.return_value = mock_chat

        session_id = "test-session-delete"
        
        # Create an agent
        agent = await get_agent_instance(session_id)
        assert session_id in _agent_sessions
        
        # Delete the agent
        result = delete_agent_instance(session_id)
        
        assert result is True
        assert session_id not in _agent_sessions

    def test_delete_nonexistent_session_returns_false(self):
        result = delete_agent_instance("nonexistent-session")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_agent_instance_requires_session_id(self):
        with pytest.raises(ValueError, match="Session ID must be provided"):
            await get_agent_instance(None)

        with pytest.raises(ValueError, match="Session ID must be provided"):
            await get_agent_instance("")

    @pytest.mark.asyncio
    @patch("src.agent.Chat.create")
    @patch("agent.Agent.initialize_mcp_tools", new_callable=AsyncMock)
    async def test_session_persistence_without_decorator(self, mock_initialize_mcp, mock_chat_create):
        """Test that session management works without @persist_session decorator"""
        mock_chat = Mock()
        mock_chat.tools = []
        mock_chat_create.return_value = mock_chat

        session_id = "test-persistence"
        
        # Get agent instance
        agent = await get_agent_instance(session_id)
        
        # Modify agent state by calling methods that previously had @persist_session
        agent._update_system_prompt()
        agent.add_tool(Mock())
        agent.enable_tool("test_tool")
        agent.disable_tool("test_tool")
        
        # Verify the same agent instance is still accessible
        same_agent = await get_agent_instance(session_id)
        assert same_agent is agent
        assert session_id in _agent_sessions
