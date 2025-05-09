from dotenv import load_dotenv
load_dotenv()

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

def run_conversation():
    
    
    while True:
        user_prompt = input("Enter your question (or type 'exit' to quit):\n")
        if user_prompt.lower() == "exit":
            break
        
        # Get initial response with potential tool calls
        response = chat.send_prompt(system_role, user_prompt)
        
        # Print final response
        print("\nResponse:")
        print(response)
        print("\n" + "-" * 50 + "\n")

if __name__ == "__main__":
    run_conversation()