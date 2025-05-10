import asyncio
import agent

from utils import graceful_exit, mainloop
from utils.mcpclient.sessions_manager import MCPSessionManager

session_manager = MCPSessionManager()

@graceful_exit
async def mcp_discovery():
    success = await session_manager.load_mcp_sessions()
    if not success:
        print("No valid MCP sessions found in configuration")
        return
    
    await session_manager.list_tools()
    for tool in session_manager.tools:
        agent.add_mcp_tool(tool)
    
    print(session_manager.sessions.keys())

@mainloop
@graceful_exit
async def mcp_ping():
    await session_manager.ping()
    print(session_manager.sessions.keys())
    await asyncio.sleep(10)

@mainloop
@graceful_exit
async def agent_task():
    await agent.run_conversation()

@graceful_exit
async def main():
    print("<Discovery: MCP Server>")
    await mcp_discovery()
    print("\n" + "-" * 50 + "\n")

    await asyncio.gather(
        mcp_ping(),
        agent_task()
    )

if __name__ == "__main__":
    asyncio.run(main())