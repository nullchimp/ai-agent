import asyncio
import agent

from utils import graceful_exit, mainloop
from utils.mcpclient.sessions_manager import MCPSessionManager

session_manager = MCPSessionManager()

@mainloop
@graceful_exit
async def agent_task():
    await agent.run_conversation()

@graceful_exit
async def main():
    await session_manager.discovery()
    for tool in session_manager.tools:
        agent.add_tool(tool)

    await agent_task()

if __name__ == "__main__":
    asyncio.run(main())