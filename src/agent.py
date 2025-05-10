from dotenv import load_dotenv
load_dotenv()

import json
from typing import Dict, Any, Generator, List

from utils import chatutil, graceful_exit
from utils.azureopenai.chat import Chat
from tools import Tool
from tools.google_search import GoogleSearch
from tools.read_file import ReadFile
from tools.write_file import WriteFile
from tools.list_files import ListFiles
from tools.web_fetch import WebFetch

tool_map = {
    "google_search": GoogleSearch(),
    "read_file": ReadFile(),
    "write_file": WriteFile(),
    "list_files": ListFiles(),
    "web_fetch": WebFetch()
}
chat = Chat.create(tool_map)
def add_mcp_tool(tool: Tool) -> None:
    tool_map[tool.name] = tool
    chat.add_tool(tool)

async def process_tool_calls(response: Dict[str, Any], call_back) -> None:
    for tool_call in response.get("tool_calls", []):
        function_data = tool_call.get("function", {})
        tool_name = function_data.get("name", "")
        if not tool_name:
            continue
        
        arguments = function_data.get("arguments", "{}")

        print(f"<Tool: {tool_name}> ", arguments)
        
        try:
            args = json.loads(arguments)
        except json.JSONDecodeError:
            args = {}

        tool_result = {
            "error": f"Tool '{tool_name}' not found"
        }

        if tool_name in tool_map:
            tool_instance = tool_map[tool_name]
            try:
                tool_result = await tool_instance.run(**args)
                print(f"<Tool Result: {tool_name}> ", tool_result)
            except Exception as e:
                tool_result = {
                    "error": f"Error running tool '{tool_name}': {str(e)}"
                }
                print(f"<Tool Error: {tool_name}> ", tool_result)
            
        call_back({
            "role": "tool",
            "tool_call_id": tool_call.get("id", "unknown_tool"),
            "content": json.dumps(tool_result)
        })

# Define enhanced system role with instructions on using all available tools
system_role = """
You are a helpful assistant. 
Your Name is Agent Smith and you have access to various capabilities:

1. Search the web for current information using the google_search tool
2. Read files from a secure directory using the read_file tool
3. Write content to files using the write_file tool
4. List files in a directory using the list_files tool
5. Fetch web pages and convert them to markdown using the web_fetch tool

Use these tools appropriately to provide comprehensive assistance.
Synthesize and cite your sources correctly when using search or web content.
"""
messages = [{"role": "system", "content": system_role}]

@graceful_exit
@chatutil("Agent")
async def run_conversation(user_prompt) -> str:
    # Example:
    # user_prompt = """
    # Who is the current chancellor of Germany? 
    # Write the result to a file with the name 'chancellor.txt' in a folder with the name 'docs'.
    # Then list me all files in my root directory and put the result in another file called 'list.txt' in the same 'docs' folder.
    # """
        
    messages.append({"role": "user", "content": user_prompt})
    response = await chat.send_messages(messages)
    choices = response.get("choices", [])
    
    assistant_message = choices[0].get("message", {})
    messages.append(assistant_message)
    
    # Handle the case where tool_calls might be missing or not a list
    while assistant_message.get("tool_calls"):
        await process_tool_calls(assistant_message, messages.append)

        response = await chat.send_messages(messages)
        if not (response and response.get("choices", None)):
            break
            
        assistant_message = response.get("choices", [{}])[0].get("message", {})
        messages.append(assistant_message)
    
    return assistant_message.get("content", "")

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_conversation())