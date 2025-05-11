
import os
import json

from typing import Any, Dict, List

from tools import Tool
from .client import Client

DEFAULT_TEMPERATURE = 0.5
DEFAULT_MAX_TOKENS = 500
DEFAULT_API_KEY_ENV = "AZURE_OPENAI_API_KEY"
DEFAULT_TIMEOUT = 30.0

class Chat:
    debug = False

    def __init__(self, client, tool_list: List[Tool] = []):
        self.client = client
        self.tool_map = {tool.name: tool for tool in tool_list}
        self.tools = [tool.define() for tool in tool_list]
    
    def add_tool(self, tool: Tool) -> None:
        self.tool_map[tool.name] = tool
        self.tools.append(tool.define())

    @classmethod
    def create(cls, tool_list = []) -> 'Chat':
        api_key = os.environ.get(DEFAULT_API_KEY_ENV)
        if not api_key:
            raise ValueError(f"{DEFAULT_API_KEY_ENV} environment variable is required")
        
        client = Client(api_key=api_key)

        if Chat.debug:
            for tool in tool_list:
                print(f"<Tool Initialized: {tool.name}>")
            print("\n")

        return cls(client, tool_list)
    
    async def send_messages(
        self,
        messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        resp = await self.client.make_request(
            messages=messages,
            temperature=0.7,
            max_tokens=32000,
            tools=self.tools
        )
        
        return resp
    
    async def process_tool_calls(self, response: Dict[str, Any], call_back) -> None:
        for tool_call in response.get("tool_calls", []):
            function_data = tool_call.get("function", {})
            tool_name = function_data.get("name", "")
            if not tool_name:
                continue
            
            arguments = function_data.get("arguments", "{}")

            if Chat.debug:
                print(f"<Tool Call: {tool_name}> ", arguments)
            
            try:
                args = json.loads(arguments)
            except json.JSONDecodeError:
                args = {}

            tool_result = {
                "error": f"Tool '{tool_name}' not found"
            }

            if tool_name in self.tool_map:
                tool_instance = self.tool_map[tool_name]
                try:
                    tool_result = await tool_instance.run(**args)
                    if Chat.debug:
                        print(f"<Tool Result: {tool_name}> ", tool_result)
                except Exception as e:
                    tool_result = {
                        "error": f"Error running tool '{tool_name}': {str(e)}"
                    }
                    if Chat.debug:
                        print(f"<Tool Exception: {tool_name}> ", str(e))
                
            call_back({
                "role": "tool",
                "tool_call_id": tool_call.get("id", "unknown_tool"),
                "content": json.dumps(tool_result)
            })
