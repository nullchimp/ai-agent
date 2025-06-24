from dotenv import load_dotenv
load_dotenv(override=True)

import asyncio
import os
from datetime import date

from core import chatutil, graceful_exit, pretty_print
from core.llm.chat import Chat
from core.mcp.sessions_manager import MCPSessionManager

from tools import Tool
from tools.github_search import GitHubKnowledgebase
from tools.google_search import GoogleSearch
from tools.read_file import ReadFile
from tools.write_file import WriteFile
from tools.list_files import ListFiles

_agent_sessions = {}

class Agent:
    def __init__(self, session_id: str = "cli-session"):
        self.tools = {
            GitHubKnowledgebase(),
            GoogleSearch(),
            ReadFile(),
            WriteFile(),
            ListFiles(),
        }
        self.chat = Chat.create(self.tools, session_id)

        # Enable all tools by default
        for tool in self.chat.tools:
            tool.enable()

        self.session_id = session_id
        self.mcp_initialized = False

        self.history = []
        self._update_system_prompt()

    def _get_available_tools_text(self) -> str:
        enabled_tools = [tool.name for tool in self.chat.tools if tool.enabled]
        if not enabled_tools:
            return "No tools are currently available."
        return f"Currently available tools: {', '.join(enabled_tools)}"

    def _update_system_prompt(self) -> None:
        available_tools_text = self._get_available_tools_text()

        system_role = f"""
            You are a helpful assistant. 
            Your Name is Agent Smith.

            TOOL AVAILABILITY STATUS:
            {available_tools_text}
            
            NOTE: Tools can be dynamically enabled or disabled. Always work with the tools currently available to you.
            If a required tool is not available, inform the user and suggest alternatives or request tool activation.

            CRITICAL GITHUB FACT-CHECKING REQUIREMENT:
            - For ANY GitHub-related facts, claims, or information (repositories, issues, PRs, code, documentation, etc.), 
              you MUST ALWAYS validate and ground your response using the GitHub Knowledgebase tool IF AVAILABLE.
            - This requirement applies regardless of what other tools you use or what information source provided the initial data.
            - If GitHub Knowledgebase tool is not available, clearly state this limitation when discussing GitHub information.

            TOOL USAGE STRATEGY:
            
            For GitHub-related tasks:
            1. Use GitHub MCP servers or other available tools for operations (creating issues, PRs, accessing repositories, etc.)
            2. If GitHub Knowledgebase tool is available, cross-reference and validate any factual claims with it
            3. If there's a discrepancy, prioritize the GitHub Knowledgebase for factual accuracy
            4. Clearly distinguish between operational results and verified facts in your responses

            For general tasks and information gathering:
            - Use ANY available tool that best serves the task (MCP servers, Google Search, file operations, etc.)
            - Choose the most appropriate tool(s) from those currently available
            - You can combine multiple available tools to provide comprehensive solutions
            - If needed tools are not available, explain the limitation and suggest alternatives

            CORE PRINCIPLES:
            - You MUST call tools explicitly when available - never make up answers
            - If you lack sufficient information even after using available tools, say "I don't know"
            - If required tools are unavailable, clearly communicate this limitation
            - Always synthesize information from multiple sources when beneficial
            - Cite your sources clearly and keep responses concise
            - Prioritize accuracy over speed - verify facts when verification tools are available

            Today is {date.today().strftime("%d %B %Y")}.
        """

        # Update the system message in history
        if self.history and self.history[0]["role"] == "system":
            self.history[0]["content"] = system_role
        else:
            self.history.insert(0, {"role": "system", "content": system_role})

    def add_tool(self, tool: Tool) -> None:
        self.chat.add_tool(tool)
        self._update_system_prompt()

    def enable_tool(self, tool_name: str) -> bool:
        try:
            self.chat.enable_tool(tool_name)
            self._update_system_prompt()
        except Exception as e:
            return False
        return True

    def disable_tool(self, tool_name: str) -> bool:
        try:
            self.chat.disable_tool(tool_name)
            self._update_system_prompt()
        except Exception as e:
            return False
        return True

    def get_tools(self) -> list:
        return self.chat.get_tools()

    async def initialize_mcp_tools(self):
        if self.mcp_initialized:
            return

        config_path = os.path.join(os.path.dirname(__file__), "..", "config", "mcp.json")
        session_manager = MCPSessionManager()
        await session_manager.discovery(config_path)
        for tool in session_manager.tools:
            self.add_tool(tool)

        self.mcp_initialized = True

    async def process_query(self, user_prompt: str) -> str:
        user_role = {"role": "user", "content": user_prompt}

        messages = list(self.history)
        messages.append(user_role)

        response = await self.chat.send_messages(messages)
        choices = response.get("choices", [])

        assistant_message = choices[0].get("message", {})
        messages.append(assistant_message)

        tools_used = set()
        # Handle the case where tool_calls might be missing or not a list
        while assistant_message.get("tool_calls"):
            used_tools = await self.chat.process_tool_calls(
                assistant_message, messages.append
            )
            for tool in used_tools:
                tools_used.add(tool)

            response = await self.chat.send_messages(messages)
            if not (response and response.get("choices", None)):
                break

            assistant_message = response.get("choices", [{}])[0].get("message", {})
            messages.append(assistant_message)

        result = assistant_message.get("content", "")
        if result:
            self.history.append(user_role)
            self.history.append(assistant_message)

        pretty_print("History", self.history)
        return result, tools_used

def get_agent_instance(session_id: str = None) -> Agent:
    if not session_id:
        raise ValueError("Session ID must be provided to get agent instance.")
    
    if not session_id in _agent_sessions:
        _agent_sessions[session_id] = Agent(session_id)

    return _agent_sessions[session_id]


def delete_agent_instance(session_id: str) -> bool:
    from core.debug_capture import delete_debug_capture_instance
    
    if session_id in _agent_sessions:
        del _agent_sessions[session_id]
        delete_debug_capture_instance(session_id)
        return True
    return False


def add_tool(tool: Tool, session_id: str = "cli-session") -> None:
    get_agent_instance(session_id).add_tool(tool)

@graceful_exit
@chatutil("Agent")
async def run_conversation(user_prompt, session_id: str = "cli-session") -> str:
    result = await get_agent_instance(session_id).process_query(user_prompt)
    pretty_print("Result", result)
    return result


if __name__ == "__main__":
    asyncio.run(run_conversation())
