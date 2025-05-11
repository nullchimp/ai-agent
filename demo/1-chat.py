from dotenv import load_dotenv
load_dotenv()

from datetime import date

from utils import chatutil, graceful_exit, mainloop, pretty_print
from utils.azureopenai.chat import Chat

# Initialize the Chat client
chat = Chat.create()

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
@chatutil("Chat")
async def run_conversation(user_prompt: str) -> str:
    messages.append({"role": "user", "content": user_prompt})
    response = await chat.send_messages(messages)

    content = ""
    if response:
        if isinstance(response, dict) and "choices" in response:
            choices = response.get("choices", [])
            if choices and len(choices) > 0:
                message = choices[0].get("message", {})
                content = message.get("content", "")

    pretty_print(" Result ", content)

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_conversation())