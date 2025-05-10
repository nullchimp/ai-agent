from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.shared.exceptions import McpError

from utils import graceful_exit

import asyncio

class MCPSession:
    def __init__(self, server_name: str, server_config: dict):
        self.name = server_name

        if not (server_config.get("command", None)):
            raise ValueError("Invalid server configuration")

        self.server_params = StdioServerParameters(
            command=server_config.get("command", None),  # Executable
            args=server_config.get("args", []),  # Optional command line arguments
            env=server_config.get("env", None),  # Optional environment variables
        )

    @graceful_exit
    async def list_tools(self) -> ClientSession:
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(
                read, write
            ) as session:
                try:
                    await session.initialize()
                    return await session.list_tools()
                except McpError as e:
                    return []
                
    async def call_tool(self, tool_name: str, arguments: dict):
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(
                read, write
            ) as session:
                try:
                    await session.initialize()
                    res = await session.call_tool(tool_name, arguments)
                    print("T RES ", res)
                    return res
                except McpError as e:
                    return None
        return res
                
    async def send_ping(self):
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(
                read, write
            ) as session:
                try:
                    await session.initialize()
                    return await session.send_ping()
                except McpError as e:
                    return None