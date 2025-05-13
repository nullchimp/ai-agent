import os
import json

from typing import Any, Dict, List

from tools import Tool
from .client import Client

from core.pretty import prettify, colorize_text

DEFAULT_TEMPERATURE = 0.5
DEFAULT_MAX_TOKENS = 500
DEFAULT_API_KEY_ENV = "AZURE_OPENAI_API_KEY"
DEFAULT_TIMEOUT = 30.0

from core import DEBUG
class Chat:
    debug = DEBUG

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
                print(colorize_text(f"<Tool Initialized: {colorize_text(tool.name, "yellow")}>", "cyan"))
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
        hr = "#" * 50
        name = "Agent -> Tools"
        if Chat.debug:
            print(colorize_text(f"\n{hr} <{name}> {hr}\n", "yellow"))
            
        # Safely get tool_calls - convert None to empty list to handle the case when tool_calls is None
        tool_calls = response.get("tool_calls", [])
        for tool_call in tool_calls:
            function_data = tool_call.get("function", {})
            tool_name = function_data.get("name", "")
            if not tool_name:
                continue
            
            arguments = function_data.get("arguments", "{}")

            if Chat.debug:
                print(colorize_text(f"<Tool Call: {colorize_text(tool_name, "green")}> ", "yellow"), arguments)
            
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
                        print(colorize_text(f"<Tool Result: {colorize_text(tool_name, "green")}> ", "yellow"), prettify(tool_result))
                except Exception as e:
                    tool_result = {
                        "error": f"Error running tool '{tool_name}': {str(e)}"
                    }
                    if Chat.debug:
                        print(colorize_text(f"<Tool Exception: {colorize_text(tool_name, "red")}> ", "yellow"), str(e))
            
            if Chat.debug:
                print(colorize_text(f"\n####{hr * 2}{"#" * len(name)}", "yellow"))

            call_back({
                "role": "tool",
                "tool_call_id": tool_call.get("id", "unknown_tool"),
                "content": json.dumps(tool_result)
            })
