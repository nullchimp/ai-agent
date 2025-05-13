"""Session manager for MCP connections."""
from typing import Dict, Optional, List
import json
import os

from tools import Tool
from core.mcpclient import session as mcp

from core import DEBUG, colorize_text
class MCPSessionManager:
    debug = DEBUG

    def __init__(self) -> None:
        self._sessions: Dict[str, mcp.MCPSession] = {}
        self._tools: List[Tool] = []

    async def discovery(self, config_path) -> None:
        if MCPSessionManager.debug:
            print(colorize_text("<Discovery: MCP Server>", "grey"))

        success = await self.load_mcp_sessions(config_path)
        if not success:
            print("No valid MCP sessions found in configuration")
            return
        
        await self.list_tools()

        if MCPSessionManager.debug:
            for server_name, session in self._sessions.items():
                print(colorize_text(f"\n<Active MCP Server: {colorize_text(server_name, "magenta")}>", "cyan"))
                for tool in session.tools:
                    print(colorize_text(f"<Tool Initialized: {colorize_text(tool.name, "yellow")}>", "cyan"))
            print("\n")

    async def load_mcp_sessions(self, config_path) -> Dict[str, mcp.MCPSession]:
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            for server_name, server_config in config.get('servers', {}).items():
                session = mcp.MCPSession(server_name, server_config)
                self._sessions[server_name] = session
            return True
        except FileNotFoundError:
            print(f"Configuration file not found: {config_path}")
        except json.JSONDecodeError:
            print(f"Invalid JSON in configuration file: {config_path}")
        except Exception as e:
            print(f"Error loading MCP sessions: {e}")

        return None

    async def list_tools(self) -> None:
        self._tools = []
        for server_name, session in self._sessions.items():
            try:
                tools = await session.list_tools()
                self._tools += tools
            except Exception as e:
                print(f"Error listing tools for server {server_name}: {e}")
                
    @property
    def sessions(self) -> Dict[str, mcp.MCPSession]:
        return self._sessions
    
    @property
    def tools(self) -> List[Tool]:
        return self._tools