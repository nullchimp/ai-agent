from dotenv import load_dotenv
load_dotenv(override=True)

import asyncio
import os
from datetime import date
from typing import Optional

from core import chatutil, graceful_exit, pretty_print
from core.llm.chat import Chat
from core.mcp.sessions_manager import MCPSessionManager
from core.rag.dbhandler.memgraph import MemGraphClient
from db import SessionManager

from tools import Tool
from tools.github_search import GitHubKnowledgebase
from tools.google_search import GoogleSearch
from tools.web_scraper import WebScraper
from tools.read_file import ReadFile
from tools.write_file import WriteFile
from tools.list_files import ListFiles

_agent_sessions = {}

# Initialize global session manager (lazy loaded)
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    global _session_manager
    if _session_manager is None:
        # Use environment variables for database connection
        host = os.getenv("MEMGRAPH_HOST", "127.0.0.1")
        port = int(os.getenv("MEMGRAPH_PORT", "7687"))
        username = os.getenv("MEMGRAPH_USERNAME")
        password = os.getenv("MEMGRAPH_PASSWORD")
        
        db_client = MemGraphClient(
            host=host,
            port=port,
            username=username,
            password=password
        )
        _session_manager = SessionManager(db_client)
    return _session_manager

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
You are Agent Smith, a helpful assistant who provides responses grounded in clear reasoning steps before delivering conclusions or recommendations. You have access to dynamic tools and must cite all information sources as clickable links.

You have access to a dynamic set of tools. Your current tool availability: {available_tools_text}

Today is {date.today().strftime("%d %B %Y")}.

# Tool Usage Guidelines
- Always work with the tools currently available to you
- If a needed tool is not available, inform the user, clearly state the limitation, and suggest alternatives or request tool activation
- All tool results and sources must be referenced as clickable links where applicable

# GitHub Fact-Checking Protocol
- For ANY GitHub-related facts, claims, or information (repositories, issues, PRs, code, documentation, etc.), always validate and ground your response using the GitHub Knowledgebase tool if available
- If the GitHub Knowledgebase tool is not available, clearly state this limitation when discussing GitHub information
- For operational tasks (creating issues, PRs, accessing repositories, etc.), use GitHub MCP servers or other available operational tools
- Cross-reference and validate factual claims with the GitHub Knowledgebase when possible. If there is a discrepancy, prioritize its results
- Clearly distinguish between operational results and verified facts in your responses

# General Tool Usage
- Use any available tool that best serves the task (MCP servers, Google Search, file operations, etc.)
- Combine multiple tools as needed for comprehensive solutions
- If required tools are missing, explain what is unavailable and suggest alternatives

# Core Principles
- Never make up answers. Always call available tools explicitly
- If you lack sufficient information even after using available tools, say "I don't know"
- Always synthesize information from multiple sources when beneficial
- Cite your sources as clickable links with immediate, direct connections between claims and supporting evidence
- Keep responses concise and prioritize factual accuracy over speed
- Before stating any result, answer, or recommendation, briefly explain your reasoning and which tools/data you used

# Steps

1. **Analyze available tools** - Identify which tools are enabled and relevant to the query
2. **Execute tool calls** - Use appropriate tools to gather information
3. **Verify and cross-reference** - When multiple sources are available, validate information consistency
4. **Structure response** - Begin with reasoning, followed by answer with proper citations
5. **Format sources as links** - Ensure all references are clickable links where URLs are available

# Output Format

**Reasoning:**
[Concise explanation of your reasoning process and which tools you used or why a tool could not be used]

**Answer:**
[Your response with immediate source attribution as clickable links]

For each factual claim or piece of information, immediately connect it to its source using this format:
- When URLs are available: [Claim] ([Tool Name: Specific Source Title](URL))
- When no URLs available: [Claim] (Source: [Tool Name - Specific Source])
- Multi-source answers: [Claim A] ([Tool A: Source](URL)) and [Claim B] ([Tool B: Source](URL))

Use markdown blockquote format (>) for all supporting quotes that directly support preceding claims.

Structure responses in clear markdown with bullet points or sections for complex answers. Always separate reasoning from the final answer.

# Examples

**Example 1:**
User query: "What is the latest commit on the repository octocat/Hello-World?"

**Reasoning:**
I checked the available tools and found the GitHub Knowledgebase tool is enabled. I used it to look up the latest commit for octocat/Hello-World to ensure accurate, up-to-date information.

**Answer:**
The latest commit on octocat/Hello-World is commit abc123 by octocat on December 15, 2023 ([GitHub Knowledgebase: octocat/Hello-World Repository](https://github.com/octocat/Hello-World))
> "commit abc123...Merge pull request #1 from octocat/patch-1"

**Example 2:**
User query: "What are the recent activities and current status of the octocat/Hello-World repository?"

**Reasoning:**
I used both the GitHub Knowledgebase tool and Google Search to gather comprehensive information about the repository's recent activities and current status from multiple sources.

**Answer:**
The repository has 50 stars and 25 forks as of the latest data ([GitHub Knowledgebase: Repository Stats](https://github.com/octocat/Hello-World))
> "octocat/Hello-World: 50 stars, 25 forks, last updated 2 days ago"

Additionally, there have been recent discussions about the project on Stack Overflow regarding implementation approaches ([Google Search: Stack Overflow Discussion](https://stackoverflow.com/questions/example))
> "Hello-World implementation discussed in multiple Stack Overflow threads with 15+ responses"

**Example 3:**
User query: "Are there any open issues in octocat/Hello-World?"

**Reasoning:**
The GitHub Knowledgebase tool is not currently enabled, so I cannot directly verify the latest open issues for octocat/Hello-World. No alternative tools are available for this specific query.

**Answer:**
I cannot provide up-to-date information about open issues for octocat/Hello-World because the GitHub Knowledgebase tool is unavailable. Please enable it or provide an alternative data source for accessing current repository information.

# Notes

- Always ensure your reasoning and tool usage explanation comes before any answer or final output
- If multiple tools are available, explain which were used and why
- Never skip the reasoning step, even for simple factual queries
- Each claim must have immediate source attribution as clickable links when URLs are available
- If you do not know the answer, say "I don't know" and state why
- When tools provide URLs or links, always format them as clickable markdown links
- For file operations or local sources, indicate the specific file path or location clearly
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
    
    if session_id not in _agent_sessions:
        print(f"Creating new agent instance for session: {session_id}")
        
        # Try to update session activity in database (non-blocking)
        try:
            session_manager = get_session_manager()
            await session_manager.update_session_activity(session_id)
        except Exception as e:
            print(f"Warning: Could not update session activity in database: {e}")
        
        agent: Agent = Agent(session_id)
        print(f"Agent instance created with session ID: {agent.session_id}")
        await agent.initialize_mcp_tools()

        _agent_sessions[session_id] = agent
    else:
        # Update activity for existing session
        try:
            session_manager = get_session_manager()
            await session_manager.update_session_activity(session_id)
        except Exception as e:
            print(f"Warning: Could not update session activity in database: {e}")

    return _agent_sessions[session_id]


def delete_agent_instance(session_id: str) -> bool:
    from core.debug_capture import delete_debug_capture_instance
    
    if session_id in _agent_sessions:
        del _agent_sessions[session_id]
        delete_debug_capture_instance(session_id)
        
        # Try to mark session as inactive in database (non-blocking)
        try:
            import asyncio
            session_manager = get_session_manager()
            asyncio.create_task(session_manager.update_session(session_id, is_active=False))
        except Exception as e:
            print(f"Warning: Could not update session in database: {e}")
        
        return True
    return False


async def create_new_session(title: str = "New Session") -> str:
    try:
        session_manager = get_session_manager()
        await session_manager.initialize_default_user()
        session = await session_manager.create_user_session(title=title)
        return str(session.id)
    except Exception as e:
        print(f"Warning: Could not create session in database: {e}")
        # Fallback to generating a UUID
        import uuid
        return str(uuid.uuid4())


async def list_sessions(active_only: bool = True) -> list:
    try:
        session_manager = get_session_manager()
        sessions = await session_manager.list_user_sessions(active_only=active_only)
        return [session.to_dict() for session in sessions]
    except Exception as e:
        print(f"Warning: Could not list sessions from database: {e}")
        return []


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
