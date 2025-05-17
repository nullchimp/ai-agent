from dotenv import load_dotenv

# Force reload of environment variables to avoid cached data
load_dotenv(override=True)

from core.azureopenai.client import Client
from core.rag.embedder import TextEmbedding3Small
from core.rag.graph_client import MemGraphClient

import asyncio
import os

#################################################

from core import pretty_print
from datetime import date
from core.azureopenai.chat import Chat

# Initialize the Chat client
chat = Chat.create()

# Define enhanced system role with instructions on using all available tools
system_role = f"""
You are an expert on everything GitHub.
Your Name is Agent Smith.

Your goal is to criticly answer the user's question, based on the information you get.
SOmetimes the user

Today is {date.today().strftime("%d %B %Y")}.
"""

messages = [{"role": "system", "content": system_role}]

async def run_conversation(user_prompt: str, rag_prompt) -> str:
    messages.append({"role": "system", "content": rag_prompt})
    messages.append({"role": "user", "content": user_prompt})
    response = await chat.send_messages(messages)

    content = ""
    if response:
        if isinstance(response, dict) and "choices" in response:
            choices = response.get("choices", [])
            if choices and len(choices):
                message = choices[0].get("message", {})
                content = message.get("content", "")

    pretty_print(" Result ", content)

#################################################

# Set up clients
api_key = os.environ.get("AZURE_OPENAI_API_KEY")
if not api_key:
    raise ValueError(f"AZURE_OPENAI_API_KEY environment variable is required")

db = MemGraphClient(
    host=os.environ.get("MEMGRAPH_URI", "localhost"),
    port=int(os.environ.get("MEMGRAPH_PORT", 7687)),
    username=os.environ.get("MEMGRAPH_USERNAME", "memgraph"),
    password=os.environ.get("MEMGRAPH_PASSWORD", "memgraph"),
)

embedder = TextEmbedding3Small()

async def test_vector_search():
    query_text = "How do Premium Requests work?"
    print(f"Using query text (truncated): {query_text[:100]}...")

    # 6. Load a vector store to use for search
    vector_store = db.load_vector_store(model=embedder.model)
    if not vector_store:
        print(f"No vector store found for model {embedder.model}")
        return
    
    query_embedding = await embedder.get_embedding(query_text)
    
    print(f"Using vector store: {vector_store.id} (model: {vector_store.model})")
    
    # 7. Perform vector search
    index_name = vector_store.metadata.get("index_name", None)
    if not index_name:
        print("No index name found in vector store metadata")
        return
    search_results = db.search_chunks(
        query_vector=query_embedding,
        index_name=index_name,
        k=10
    )
    
    # 8. Display results
    print("\n----- Search Results -----")
    print(f"Query text: {query_text[:100]}...")
    print(f"Found {len(search_results)} results\n")
    
    rag_messages = []
    for i, result in enumerate(search_results):
        chunk = result["chunk"]
        similarity = result["similarity"]
        rag_messages.append(f"Result {i+1} (similarity: {similarity:.4f}): {chunk['content']}")

    await run_conversation(query_text, f"#Context:{"\n-".join(rag_messages)}")


async def main():
    print("Starting vector search test...")
    await test_vector_search()
    print("Test completed.")

if __name__ == "__main__":
    asyncio.run(main())