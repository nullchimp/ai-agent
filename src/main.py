from core import set_debug
set_debug(True)

import asyncio
import agent
import os

from core import graceful_exit, mainloop
from core.mcp.sessions_manager import MCPSessionManager

session_manager = MCPSessionManager()

@mainloop
@graceful_exit
async def agent_task():
    await agent.run_conversation()

@graceful_exit
async def main():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../config', 'mcp.json')
    await session_manager.discovery(path)
    for tool in session_manager.tools:
        agent.add_tool(tool)

    await agent_task()

if __name__ == "__main__":
    asyncio.run(main())