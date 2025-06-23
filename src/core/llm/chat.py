import os
import json

from typing import Any, Dict, List

from tools import Tool
from .client import ChatClient

from core import prettify, colorize_text, complex_handler

DEFAULT_TEMPERATURE = 0.5
DEFAULT_MAX_TOKENS = 500
DEFAULT_API_KEY_ENV = "AZURE_OPENAI_API_KEY"
DEFAULT_TIMEOUT = 30.0

from core import is_debug
class Chat:
    def __init__(self, tool_list: List[Tool] = []):
        self.chat_client: ChatClient = ChatClient()
        self.tool_map = {tool.name: tool for tool in tool_list}
        self.tools: List[Tool] = [tool for tool in tool_list]
    
    def add_tool(self, tool: Tool) -> None:
        self.tool_map[tool.name] = tool
        self.tools.append(tool)
        self.tools = list(set(self.tools))  # Ensure tools are unique

    def get_tools(self) -> List[Dict[str, Any]]:
        return self.tools

    def enable_tool(self, tool_name: str) -> None:
        self._set_tool_state(tool_name, active=True)

    def disable_tool(self, tool_name: str) -> None:
        self._set_tool_state(tool_name, active=False)

    def _set_tool_state(self, tool_name: str, active = True) -> None:
        for tool in self.tools:
            print(f"Checking tool: {tool.name} against {tool_name}  ")
            if tool.name != tool_name:
                continue

            tool.disable()
            if active:
                tool.enable()

            return
        
        raise ValueError(f"Tool '{tool_name}' not found in the chat tools.")

    @classmethod
    def create(cls, tool_list = []) -> 'Chat':
        api_key = os.environ.get(DEFAULT_API_KEY_ENV)
        if not api_key:
            raise ValueError(f"{DEFAULT_API_KEY_ENV} environment variable is required")
        
        if is_debug():
            for tool in tool_list:
                print(colorize_text(f"<Tool Initialized: {colorize_text(tool.name, "yellow")}>", "cyan"))
            print("\n")

        return cls(tool_list)
    
    async def send_messages(
        self,
        messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        resp = await self.chat_client.make_request(
            messages=messages,
            temperature=0.7,
            max_tokens=32000,
            tools=[tool.define() for tool in self.tools if tool.enabled],
        )
        
        return resp
    
    async def process_tool_calls(self, response: Dict[str, Any], call_back) -> None:
        hr = "#" * 50
        name = "Agent -> Tools"
        if is_debug():
            print(colorize_text(f"\n{hr} <{name}> {hr}\n", "yellow"))
            
        # Safely get tool_calls - convert None to empty list to handle the case when tool_calls is None
        tools_used = []
        tool_calls = response.get("tool_calls", [])
        for tool_call in tool_calls:
            function_data = tool_call.get("function", {})
            tool_name = function_data.get("name", "")
            if not tool_name:
                continue
            
            arguments = function_data.get("arguments", "{}")

            if is_debug():
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
                    tools_used.append(tool_name)
                    if is_debug():
                        print(colorize_text(f"<Tool Result: {colorize_text(tool_name, "green")}> ", "yellow"), prettify(tool_result))
                except Exception as e:
                    tool_result = {
                        "error": f"Error running tool '{tool_name}': {str(e)}"
                    }
                    if is_debug():
                        print(colorize_text(f"<Tool Exception: {colorize_text(tool_name, "red")}> ", "yellow"), str(e))
            
            if is_debug():
                print(colorize_text(f"\n####{hr * 2}{"#" * len(name)}", "yellow"))

            call_back({
                "role": "tool",
                "tool_call_id": tool_call.get("id", "unknown_tool"),
                "content": json.dumps(tool_result, default=complex_handler),
            })

        return tools_used
