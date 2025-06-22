from dotenv import load_dotenv
load_dotenv(override=True)

from datetime import date

from core import chatutil, graceful_exit, pretty_print
from core.llm.chat import Chat

from tools import Tool
from tools.github_search import GitHubKnowledgebase
from tools.google_search import GoogleSearch
from tools.read_file import ReadFile
from tools.write_file import WriteFile
from tools.list_files import ListFiles

class Agent:
    def __init__(self):
        self.tools = {
            GitHubKnowledgebase(),
            GoogleSearch(),
            ReadFile(),
            WriteFile(),
            ListFiles()
        }
        self.chat = Chat.create(self.tools)
        
        # Define enhanced system role with instructions on using all available tools
        self.system_role = f"""
You are a helpful assistant. 
Your Name is Agent Smith.

Whenever you are not sure about something, have a look at the tools available to you.
On GitHub related questions: 
- Use the GitHub Knowledgebase tool, which is the only reliable source.
- Only if you cannot find the answer there, use the Google Search tool, which is less reliable.

MCP Servers may provide additional tools, which you can use to execute tasks.

You MUST provide the most up-to-date and most accurate information.
You MUST synthesize and cite your sources correctly, but keep responses concise.

Today is {date.today().strftime("%d %B %Y")}.
"""

    def add_tool(self, tool: Tool) -> None:
        self.chat.add_tool(tool)

    async def process_query(self, user_prompt: str) -> str:
        messages = [{"role": "system", "content": self.system_role}]
        messages.append({"role": "user", "content": user_prompt})
        
        response = await self.chat.send_messages(messages)
        choices = response.get("choices", [])
        
        assistant_message = choices[0].get("message", {})
        messages.append(assistant_message)
        
        # Handle the case where tool_calls might be missing or not a list
        while assistant_message.get("tool_calls"):
            await self.chat.process_tool_calls(assistant_message, messages.append)
            
            response = await self.chat.send_messages(messages)
            if not (response and response.get("choices", None)):
                break
                
            assistant_message = response.get("choices", [{}])[0].get("message", {})
            messages.append(assistant_message)
        
        result = assistant_message.get("content", "")
        return result


# Global agent instance for backwards compatibility
agent_instance = Agent()

def add_tool(tool: Tool) -> None:
    agent_instance.add_tool(tool)

@graceful_exit
@chatutil("Agent")
async def run_conversation(user_prompt) -> str:
    result = await agent_instance.process_query(user_prompt)
    pretty_print("Result", result)
    return result

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_conversation())