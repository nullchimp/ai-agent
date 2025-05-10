from dotenv import load_dotenv
load_dotenv()

from utils import chatloop
from utils.azureopenai.chat import Chat

# Initialize the Chat client
chat = Chat.create()

# Define enhanced system role with instructions on using all available tools
system_role = """
You are a helpful assistant. 
Your Name is Agent Smith.

Use your knowledge to provide comprehensive assistance.
Synthesize and cite your sources correctly.
"""

messages = [{"role": "system", "content": system_role}]

@chatloop("Chat")
async def run_conversation(user_prompt):
    messages.append({"role": "user", "content": user_prompt})
    response = await chat.send_messages(messages)
    
    # Print final response
    hr = "\n" + "-" * 50 + "\n"
    print(hr, "Response:", hr)
    print(response, hr)

if __name__ == "__main__":
    run_conversation()