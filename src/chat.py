from dotenv import load_dotenv
load_dotenv()

from utils import chatutil, graceful_exit, mainloop
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

@graceful_exit
@chatutil("Chat")
async def run_conversation(user_prompt: str) -> str:
    """Run a conversation with the user.
    
    Args:
        user_prompt: The user's input prompt.
        
    Returns:
        The assistant's response as a string.
    """
    messages.append({"role": "user", "content": user_prompt})
    response = await chat.send_messages(messages)
    
    # Extract content from response, handling possible errors and edge cases
    content = ""
    if response:
        if isinstance(response, dict) and "choices" in response:
            choices = response.get("choices", [])
            if choices and len(choices) > 0:
                message = choices[0].get("message", {})
                content = message.get("content", "")
    
    # Print final response
    hr = "\n" + "-" * 50 + "\n"
    print(hr, "Response:", hr)
    print(response, hr)
    
    return content

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_conversation())