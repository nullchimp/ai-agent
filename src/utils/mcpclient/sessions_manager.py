"""Session manager for MCP connections."""
from typing import Dict, Optional, List
import json
import os
import asyncio

from tools import Tool
from utils.mcpclient import session as mcp

class MCPSessionManager:
    def __init__(self) -> None:
        self._all_sessions: Dict[str, mcp.MCPSession] = {}
        self._active_sessions: Optional[mcp.MCPSession] = {}
        self._tools: List[Tool] = []
    
    async def load_mcp_sessions(self) -> Dict[str, mcp.MCPSession]:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../config', 'mcp.json')
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            for server_name, server_config in config.get('servers', {}).items():
                session = mcp.MCPSession(server_name, server_config)
                self._active_sessions[server_name] = session
                self._all_sessions[server_name] = session

            return True
        except FileNotFoundError:
            print(f"Configuration file not found: {config_path}")
        except json.JSONDecodeError:
            print(f"Invalid JSON in configuration file: {config_path}")
        except Exception as e:
            print(f"Error loading MCP sessions: {e}")

        return None

    def _activate(self, server_name: str) -> None:
        if server_name in self._all_sessions:
            self._active_sessions[server_name] = self._all_sessions[server_name]

    def _deactivate(self, server_name: str) -> None:
        if server_name in self._active_sessions:
            del self._active_sessions[server_name]

    async def list_tools(self) -> None:
        for server_name, session in self._all_sessions.items():
            try:
                data = await session.list_tools()
                print(f"Server: {server_name}, Tools: {data}")
                if not data:
                    self._deactivate(server_name)
                    continue

                for tool_data in data:
                    if tool_data[0] != "tools":
                        continue
                    
                    for t in tool_data[1]:
                        tool = Tool(
                            session=session,
                            name=t.name,
                            description=t.description,
                            parameters=t.inputSchema
                        )
                        
                        self._tools.append(tool)
                self._activate(server_name)
            except Exception as e:
                self._deactivate(server_name)
                print(f"Error listing tools for server {server_name}: {e}")

    async def ping(self) -> None:
        for server_name, session in self._active_sessions.items():
            print(f"<Active MCP Server: {server_name}>")

        for server_name, session in self._all_sessions.items():
            try:
                await session.send_ping()
                self._activate(server_name)
            except Exception as e:
                self._deactivate(server_name)
                
    @property
    def sessions(self) -> Dict[str, mcp.MCPSession]:
        return self._active_sessions
    
    @property
    def tools(self) -> List[Tool]:
        return self._tools