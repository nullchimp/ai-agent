from dotenv import load_dotenv
load_dotenv()

import json
from typing import Dict, List, Any

from utils.azureopenai.chat import Chat
from tools.google_search import GoogleSearch
from tools.read_file import ReadFile
from tools.write_file import WriteFile
from tools.list_files import ListFiles
from tools.web_fetch import WebFetch

# Initialize the Chat client
chat = Chat.create()

# Create instances of all available tools
search_tool = GoogleSearch()
read_file_tool = ReadFile()
write_file_tool = WriteFile()
list_files_tool = ListFiles()
web_fetch_tool = WebFetch()

# Map tool names to their instances for easy lookup
tool_map = {
    "google_search": search_tool,
    "read_file": read_file_tool,
    "write_file": write_file_tool,
    "list_files": list_files_tool,
    "web_fetch": web_fetch_tool
}

# Add all tools to the tools list
tools = [
    search_tool.define(),
    read_file_tool.define(),
    write_file_tool.define(),
    list_files_tool.define(),
    web_fetch_tool.define()
]

def process_tool_calls(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    tool_results = []
    
    # Check for tool calls in the response
    if "tool_calls" in response:
        for tool_call in response.get("tool_calls", []):
            tool_name = tool_call.get("function", {}).get("name")
            arguments = tool_call.get("function", {}).get("arguments", "{}")
            
            # Parse the arguments
            try:
                args = json.loads(arguments)
            except json.JSONDecodeError:
                args = {}
            
            print(f"Executing tool: {tool_name} with arguments: {args}")

            # Execute the tool if it exists in our map
            if tool_name in tool_map:
                tool_instance = tool_map[tool_name]
                tool_result = tool_instance.run(**args)
                
                # Prepare the tool result for the API
                tool_results.append({
                    "tool_call_id": tool_call.get("id"),
                    "output": json.dumps(tool_result)
                })
            else:
                # If tool doesn't exist, return an error
                tool_results.append({
                    "tool_call_id": tool_call.get("id"),
                    "output": json.dumps({
                        "error": f"Tool '{tool_name}' not found"
                    })
                })
                
    return tool_results

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

def run_conversation():
    
    messages = [{"role": "system", "content": system_role}]
    
    while True:
        user_prompt = input("Enter your question (or type 'exit' to quit):\n")
        if user_prompt.lower() == "exit":
            break
            
        messages.append({"role": "user", "content": user_prompt})
        
        # Get initial response with potential tool calls
        response = chat.send_prompt_with_messages_and_options(messages, tools)
        
        # Extract the message content
        assistant_message = response.get("choices", [{}])[0].get("message", {})
        messages.append(assistant_message)
        
        # Process tool calls if present
        while "tool_calls" in assistant_message:
            print("Processing tool calls...")
            
            # Execute tool calls
            tool_results = process_tool_calls(assistant_message)
            
            for result in tool_results:
                # Add tool results to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": result["tool_call_id"],
                    "content": result["output"]
                })
            
            # Get follow-up response after tool usage
            response = chat.send_prompt_with_messages_and_options(messages, tools)
            assistant_message = response.get("choices", [{}])[0].get("message", {})
            messages.append(assistant_message)
        
        # Print final response
        print("\nResponse:")
        print(assistant_message.get("content", ""))
        print("\n" + "-" * 50 + "\n")

if __name__ == "__main__":
    run_conversation()