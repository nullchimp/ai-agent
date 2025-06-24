import asyncio
import agent
import os
import argparse

from core import graceful_exit, mainloop
from core.mcp.sessions_manager import MCPSessionManager

@mainloop
@graceful_exit
async def agent_task():
    await agent.run_conversation()

@graceful_exit
async def cli_main():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../config', 'mcp.json')
   
    session_manager = MCPSessionManager()
    await session_manager.discovery(path)
    for tool in session_manager.tools:
        await agent.add_tool(tool)

    await agent_task()

def start_api_server():
    import uvicorn
    from api.app import create_app
    
    app = create_app()
    
    host = os.getenv("API_HOST", "localhost")
    port = int(os.getenv("API_PORT", "5555"))
    
    uvicorn.run(app, host=host, port=port)

def main():
    parser = argparse.ArgumentParser(description="Run the AI Agent in CLI or API mode.")
    parser.add_argument("--api", action="store_true", help="Run in API server mode.")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode.")
    args = parser.parse_args()

    if args.debug:
        from core import set_debug
        set_debug(True)

    if args.api:
        start_api_server()
        return
    
    asyncio.run(cli_main())

if __name__ == "__main__":
    main()