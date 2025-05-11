from dotenv import load_dotenv
load_dotenv()

from datetime import date

from utils import chatutil, graceful_exit, mainloop, pretty_print
from utils.azureopenai.chat import Chat
from utils.azureopenai.client import Client

from tools.google_search import GoogleSearch

Chat.debug = True
Client.debug = True

tools = [
    GoogleSearch("google_search"),
]
chat = Chat.create(tools)

# Define enhanced system role with instructions on using all available tools
system_role = f"""
You are a helpful assistant. 
Your Name is Agent Smith.

Use your knowledge to provide comprehensive assistance.
Synthesize and cite your sources correctly.

Today is {date.today().strftime("%d %B %Y")}.
"""

messages = [{"role": "system", "content": system_role}]

@mainloop
@graceful_exit
@chatutil("Chat-Tool-Exec")
async def run_conversation(user_prompt: str) -> str:
    messages.append({"role": "user", "content": user_prompt})
    response = await chat.send_messages(messages)
    choices = response.get("choices", [])
    
    assistant_message = choices[0].get("message", {})
    messages.append(assistant_message)
    
    # Handle the case where tool_calls might be missing or not a list
    while assistant_message.get("tool_calls"):
        await chat.process_tool_calls(assistant_message, messages.append)

        response = await chat.send_messages(messages)
        if not (response and response.get("choices", None)):
            break
            
        assistant_message = response.get("choices", [{}])[0].get("message", {})
        messages.append(assistant_message)
    
    result = assistant_message.get("content", "")

    hr = "\n" + "-" * 50 + "\n"
    print(hr, f"<Response> {result}", hr)

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_conversation())