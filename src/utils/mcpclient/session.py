from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.shared.exceptions import McpError

from utils import graceful_exit

class MCPSession:
    def __init__(self, server_name: str, server_config: dict):
        self.name = server_name

        if not (server_config.get("command", None)):
            raise ValueError("Invalid server configuration")

        self.exit_stack = AsyncExitStack()
        self.server_params = StdioServerParameters(
            command=server_config.get("command", None),  # Executable
            args=server_config.get("args", []),  # Optional command line arguments
            env=server_config.get("env", None),  # Optional environment variables
        )

        self._session = None

    @graceful_exit
    async def list_tools(self) -> ClientSession:
        session = await self.get_session()
        try:
            await session.initialize()
            return await session.list_tools()
        except McpError as e:
            return []
                
    async def call_tool(self, tool_name: str, arguments: dict):
        session = await self.get_session()
        try:
            await session.initialize()
            return await session.call_tool(tool_name, arguments)
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