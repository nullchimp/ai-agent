from contextlib import AsyncExitStack

from tools import Tool

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.shared.exceptions import McpError

from core import prettify, get_debug_capture

from core import is_debug, graceful_exit, colorize_text
class MCPSession:
    def __init__(self, server_name: str, server_config: dict):
        self.name = server_name

        if not (server_config.get("command", None)):
            raise ValueError("Invalid server configuration")

        self.exit_stack = AsyncExitStack()
        self.server_params = StdioServerParameters(
            command=server_config.get("command", None),  # Executable
            args=server_config.get("args", []),  # Optional command line arguments
            env=self._parse_env(server_config.get("env", None)),  # Optional environment variables
        )

        self._session = None
        self._tools = []

    @graceful_exit
    async def list_tools(self) -> ClientSession:
        session = await self.get_session()
        try:
            await session.initialize()
            data = await session.list_tools()
            if is_debug():
                print(colorize_text(f"<MCP: {self.name}>", "magenta"))
                print(colorize_text(f"<MCP: Tool Discovery Response> {prettify(data)}", "magenta"))
            if not data:
                return []

            for tool_data in data:
                if tool_data[0] != "tools":
                    continue
                
                self._tools = []
                for t in tool_data[1]:
                    tool = Tool(
                        session=self,
                        name=t.name,
                        description=t.description,
                        parameters=t.inputSchema,
                        source=self.name
                    )
                    
                    self._tools.append(tool)
                break
            return self._tools
        except McpError as e:
            return []

    @property
    def tools(self):
        return self._tools

    async def call_tool(self, tool_name: str, arguments: dict):
        session = await self.get_session()
        try:
            await session.initialize()
            if is_debug():
                print(colorize_text(f"<MCP Tool Call: Request> {prettify(arguments)}", "magenta"))
            debug_capture = get_debug_capture()
            if debug_capture:
                debug_capture.capture_mcp_call(tool_name, arguments)
            result = await session.call_tool(tool_name, arguments)
            if is_debug():
                print(colorize_text(f"<MCP Tool Call: Response> {prettify(result)}", "magenta"))
            if debug_capture:
                debug_capture.capture_mcp_result(tool_name, result)
            return result
        except McpError as e:
            return None
                
    async def send_ping(self):
        session = await self.get_session()
        try:
            await session.initialize()
            return await session.send_ping()
        except McpError as e:
            return None
        
    async def get_session(self):
        if self._session:
            return self._session
        
        stdio, write = await self.exit_stack.enter_async_context(stdio_client(self.server_params))
        self._session = await self.exit_stack.enter_async_context(ClientSession(stdio, write))
        
        return self._session
    
    def _parse_env(self, env: dict) -> dict:
        import os
        if not env:
            return None
        
        parsed_env = {}
        for key, value in env.items():
            parsed_env[key] = value

            # Check if the value is a string and starts with '$' indicating an environment variable
            if isinstance(value, str) and value.startswith("$"):
                # Replace with environment variable value
                parsed_env[key] = os.getenv(value[1:], "")

        return parsed_env