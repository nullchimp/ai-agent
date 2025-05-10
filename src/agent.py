from dotenv import load_dotenv
load_dotenv()

import json
from typing import Dict, Any

from utils import chatloop

from utils.azureopenai.chat import Chat
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

def process_tool_calls(response: Dict[str, Any]):
    for tool_call in response.get("tool_calls", []):
        tool_name = tool_call.get("function", {}).get("name")
        arguments = tool_call.get("function", {}).get("arguments", "{}")

        print(f"<Tool: {tool_name}>")
        
        try:
            args = json.loads(arguments)
        except json.JSONDecodeError:
            args = {}

        tool_result = {
            "error": f"Tool '{tool_name}' not found"
        }

        if tool_name in tool_map:
            tool_instance = tool_map[tool_name]
            tool_result = tool_instance.run(**args)
            
        yield {
            "role": "tool",
            "tool_call_id": tool_call.get("id"),
            "content": json.dumps(tool_result)
        }

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

chat = Chat.create(tool_map)
messages = [{"role": "system", "content": system_role}]

@chatloop("Agent")
async def run_conversation(user_prompt):
    # Example:
    # user_prompt = """
    # Who is the current chancellor of Germany? 
    # Write the result to a file with the name 'chancellor.txt' in a folder with the name 'docs'.
    # Then list me all files in my root directory and put the result in another file called 'list.txt' in the same 'docs' folder.
    # """
        
    messages.append({"role": "user", "content": user_prompt})
    response = await chat.send_messages(messages)

    assistant_message = response.get("choices", [{}])[0].get("message", {})
    messages.append(assistant_message)
    
    while assistant_message.get("tool_calls", False):
        for result in process_tool_calls(assistant_message):
            messages.append(result)

        response = await chat.send_messages(messages)
        assistant_message = response.get("choices", [{}])[0].get("message", {})
        messages.append(assistant_message)
    
    return assistant_message.get("content", "")

if __name__ == "__main__":
    run_conversation()