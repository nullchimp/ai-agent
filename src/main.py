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
async def cli_main():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../config', 'mcp.json')
    await session_manager.discovery(path)
    for tool in session_manager.tools:
        agent.add_tool(tool)

    await agent_task()

def start_api_server():
    import uvicorn
    from api.app import create_app
    
    app = create_app()
    
    host = os.getenv("API_HOST", "localhost")
    port = int(os.getenv("API_PORT", "5555"))
    
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    # Check if we should start the API server or run CLI mode
    if os.getenv("API_MODE", "cli").lower() == "api":
        start_api_server()
    else:
        asyncio.run(cli_main())