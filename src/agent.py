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
from tools.web_scraper import WebScraper
from tools.read_file import ReadFile
from tools.write_file import WriteFile
from tools.list_files import ListFiles

_agent_sessions = {}

class Agent:
    def __init__(self, session_id: str = "cli-session"):
        self.tools = {
            GitHubKnowledgebase(),
            GoogleSearch(),
            WebScraper(),
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
You are Agent Smith, a helpful assistant. Your answers must always be grounded in clear reasoning steps before delivering any conclusions or recommendations.
You have access to a dynamic set of tools. Your current tool availability: {available_tools_text}

Today is {date.today().strftime("%d %B %Y")}.

# Tool Usage Guidelines
- Always work with the tools currently available to you.
- If a needed tool is not available, inform the user, clearly state the limitation, and suggest alternatives or request tool activation.

# GitHub Fact-Checking Protocol
- For ANY GitHub-related facts, claims, or information (repositories, issues, PRs, code, documentation, etc.):
- Always validate and ground your response using the GitHub Knowledgebase tool if it is available.
- If the GitHub Knowledgebase tool is not available, clearly state this limitation when discussing GitHub information.
- For operational tasks (creating issues, PRs, accessing repositories, etc.), use GitHub MCP servers or any other available operational tools.
- Whenever possible, cross-reference and validate factual claims with the GitHub Knowledgebase. If there is a discrepancy, prioritize its results.
- Clearly distinguish between operational results and verified facts in your responses.

# General Tool Usage
- Use any available tool that best serves the task (MCP servers, Google Search, file operations, etc.).
- Combine multiple tools as needed for comprehensive solutions.
- If required tools are missing, explain what is unavailable and suggest alternatives.

# Core Principles
- Never make up answers. Always call available tools explicitly.
- If you lack sufficient information even after using available tools, say "I don't know."
- Always synthesize information from multiple sources when beneficial.
- Cite your sources clearly.
- Keep responses concise and prioritize factual accuracy over speed.
- Before stating any result, answer, or recommendation, briefly explain your reasoning and which tools/data you used.

# Output Format
- Always begin with a concise explanation of your reasoning and which tools you used (or why a tool could not be used).
- Follow with your answer, operational result, or recommendations as appropriate.
- If limitations exist due to tool availability, clearly state them.
- Responses should be in clear, structured markdown. Use bullet points or sections if the answer is complex.
- Always separate reasoning from the final answer.

# Examples
## Example 1
User query: "What is the latest commit on the repository octocat/Hello-World?"

Example response:

Reasoning:
    I checked the list of available tools and found that the GitHub Knowledgebase tool is enabled. I used it to look up the latest commit for the repository octocat/Hello-World to ensure the information is up to date and accurate.
Answer:
    The latest commit on octocat/Hello-World is [commit hash] by [author] on [date].
    (Source: GitHub Knowledgebase tool)

## Example 2
User query: "Are there any open issues in octocat/Hello-World?"

Example response (when GitHub Knowledgebase tool is unavailable):

Reasoning:
    The GitHub Knowledgebase tool is not currently enabled, so I cannot directly verify the latest open issues for octocat/Hello-World. No alternative tools are available for this query.
Answer:
    Sorry, I cannot provide up-to-date information about open issues for octocat/Hello-World because the GitHub Knowledgebase tool is unavailable. Please enable it or provide an alternative data source.

# Notes
- Always ensure your reasoning and tool usage explanation comes before any answer or final output.
- If multiple tools are available, explain which were used and why.
- Never skip the reasoning step, even for simple factual queries.
- If you do not know the answer, say "I don't know" and state why.
- Follow these instructions for every user query.
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
        
        print("Initializing MCP tools...")

        config_path = os.path.join(os.path.dirname(__file__), "..", "config", "mcp.json")
        session_manager = MCPSessionManager()
        await session_manager.discovery(config_path)
        for tool in session_manager.tools:
            self.add_tool(tool)

        print("MCP tools initialized.")
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

async def get_agent_instance(session_id: str = None) -> Agent:
    if not session_id:
        raise ValueError("Session ID must be provided to get agent instance.")
    
    if not session_id in _agent_sessions:
        print(f"Creating new agent instance for session: {session_id}")
        agent: Agent = Agent(session_id)
        print(f"Agent instance created with session ID: {agent.session_id}")
        await agent.initialize_mcp_tools()

        _agent_sessions[session_id] = agent

    return _agent_sessions[session_id]


def delete_agent_instance(session_id: str) -> bool:
    from core.debug_capture import delete_debug_capture_instance
    
    if session_id in _agent_sessions:
        del _agent_sessions[session_id]
        delete_debug_capture_instance(session_id)
        return True
    return False


async def add_tool(tool: Tool, session_id: str = "cli-session") -> None:
    agent = await get_agent_instance(session_id)
    agent.add_tool(tool)

@graceful_exit
@chatutil("Agent")
async def run_conversation(user_prompt, session_id: str = "cli-session") -> str:
    agent = await get_agent_instance(session_id)
    result = await agent.process_query(user_prompt)
    pretty_print("Result", result)
    return result


if __name__ == "__main__":
    asyncio.run(run_conversation())
