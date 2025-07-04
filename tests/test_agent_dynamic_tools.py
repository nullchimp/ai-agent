import pytest
from unittest.mock import Mock, patch
from agent import Agent


class TestAgentDynamicTools:
    @pytest.fixture
    def agent(self):
        with patch("src.agent.Chat.create") as mock_chat_create:
            mock_chat = Mock()
            mock_chat.tools = []
            mock_chat_create.return_value = mock_chat

            agent = Agent()
            # Add some mock tools
            for i, name in enumerate(
                ["GitHubKnowledgebase", "GoogleSearch", "ReadFile"]
            ):
                tool = Mock()
                tool.name = name
                tool.enabled = True
                tool.enable = Mock()
                tool.disable = Mock()
                mock_chat.tools.append(tool)

            # Update the system prompt with the mock tools
            agent._update_system_prompt()
            return agent

    def test_system_prompt_includes_available_tools(self, agent):
        system_message = agent.history[0]["content"]
        assert (
            "Currently available tools: GitHubKnowledgebase, GoogleSearch, ReadFile"
            in system_message
        )

    def test_system_prompt_updates_when_tool_disabled(self, agent):
        # Disable a tool
        agent.chat.tools[0].enabled = False
        agent._update_system_prompt()

        system_message = agent.history[0]["content"]
        assert "Currently available tools: GoogleSearch, ReadFile" in system_message

    def test_system_prompt_shows_no_tools_when_all_disabled(self, agent):
        # Disable all tools
        for tool in agent.chat.tools:
            tool.enabled = False
        agent._update_system_prompt()

        system_message = agent.history[0]["content"]
        assert "No tools are currently available." in system_message

    def test_enable_tool_updates_system_prompt(self, agent):
        with patch.object(agent.chat, "enable_tool") as mock_enable:
            agent.enable_tool("TestTool")
            mock_enable.assert_called_once_with("TestTool")

    def test_disable_tool_updates_system_prompt(self, agent):
        with patch.object(agent.chat, "disable_tool") as mock_disable:
            agent.disable_tool("TestTool")
            mock_disable.assert_called_once_with("TestTool")

    def test_github_knowledgebase_requirement_conditional(self, agent):
        system_message = agent.history[0]["content"]

        # When GitHub Knowledgebase is available
        assert (
            "always validate and ground your response using the GitHub Knowledgebase tool if available"
            in system_message
        )
        assert (
            "If the GitHub Knowledgebase tool is not available, clearly state this limitation"
            in system_message
        )

    def test_tool_availability_status_section_present(self, agent):
        system_message = agent.history[0]["content"]
        assert "Your current tool availability:" in system_message
        assert "You have access to a dynamic set of tools" in system_message

    def test_graceful_handling_when_required_tools_unavailable(self, agent):
        system_message = agent.history[0]["content"]
        assert (
            "If a needed tool is not available, inform the user, clearly state the limitation"
            in system_message
        )
        assert (
            "If required tools are missing, explain what is unavailable and suggest alternatives"
            in system_message
        )
