"""Session manager for MCP connections."""
from typing import Dict, Optional, List
import json
import os
import asyncio

from tools import Tool
from utils.mcpclient import session as mcp

class MCPSessionManager:
    def __init__(self) -> None:
        self._sessions: Dict[str, mcp.MCPSession] = {}
        self._tools: List[Tool] = []
    
    async def load_mcp_sessions(self) -> Dict[str, mcp.MCPSession]:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../config', 'mcp.json')
        
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
        for server_name, session in self._sessions.items():
            try:
                data = await session.list_tools()
                if not data:
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
            except Exception as e:
                print(f"Error listing tools for server {server_name}: {e}")
                
    @property
    def sessions(self) -> Dict[str, mcp.MCPSession]:
        return self._sessions
    
    @property
    def tools(self) -> List[Tool]:
        return self._tools