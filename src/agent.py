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

            On GitHub related questions: 
            - You MUST always use the GitHub Knowledgebase tool, which is the only reliable source.
            - Never make up answers, ALWAYS back them up with facts from the GitHub Knowledgebase.

            On general questions or when the GitHub Knowledgebase does not have the answer:
            - You can use the Google Search tool to find information.
            - You can also use the Read File tool to read files, Write File tool to write files, and List Files tool to list files.
            - If you need to use a tool, you MUST call it explicitly.

            On any task that requires external information:
            - You MUST use the tools provided to you by MCP Servers.
            - You MUST NOT make up answers or provide information without using the tools.
            - If you do not know the answer, you MUST say "I don't know" instead of making up an answer.

            You MUST provide the most up-to-date and most accurate information.
            You MUST synthesize and cite your sources correctly, but keep responses concise.

            Today is {date.today().strftime("%d %B %Y")}.
        """

        self.history = [
            {"role": "system", "content": self.system_role}
        ]

    def add_tool(self, tool: Tool) -> None:
        self.chat.add_tool(tool)

    async def process_query(self, user_prompt: str) -> str:
        user_role = {"role": "user", "content": user_prompt}

        messages = list(self.history)
        messages.append(user_role)
        
        response = await self.chat.send_messages(messages)
        choices = response.get("choices", [])
        
        assistant_message = choices[0].get("message", {})
        messages.append(assistant_message)
        
        tools_used = set()
        # Handle the case where tool_calls might be missing or not a list
        while assistant_message.get("tool_calls"):
            used_tools = await self.chat.process_tool_calls(assistant_message, messages.append)
            for tool in used_tools:
                tools_used.add(tool)

            response = await self.chat.send_messages(messages)
            if not (response and response.get("choices", None)):
                break
                
            assistant_message = response.get("choices", [{}])[0].get("message", {})
            messages.append(assistant_message)
        
        result = assistant_message.get("content", "")
        if result:
            self.history.append(user_role)
            self.history.append(assistant_message)
            
        pretty_print("History", self.history)
        return result, tools_used


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