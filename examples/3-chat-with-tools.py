from core import set_debug
set_debug(True)

from dotenv import load_dotenv
# Force reload of environment variables to avoid cached data
load_dotenv(override=True)

from datetime import date

from core import chatutil, graceful_exit, mainloop, pretty_print
from core.llm.chat import Chat
from core.llm.client import Client

from tools.write_file import WriteFile
from tools.google_search import GoogleSearch

tools = [
    GoogleSearch("google_search"),
    WriteFile("write_file"),
]
chat = Chat.create(tools)

# Define enhanced system role with instructions on using all available tools
system_role = f"""
You are a helpful assistant. 
Your Name is Agent Smith.

Whenever you are not sure about something, have a look at the tools available to you.
You can use them to get information or perform tasks.

You have to provide the most up-to-date information.
Synthesize and cite your sources correctly, but keep responses concise.

Today is {date.today().strftime("%d %B %Y")}.
"""

messages = [{"role": "system", "content": system_role}]

@mainloop
@graceful_exit
@chatutil("Chat-With-Tools")
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

    pretty_print(" Result ", result)

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_conversation())