from dotenv import load_dotenv

# Force reload of environment variables to avoid cached data
load_dotenv(override=True)

from core.llm.client import Client
from core.rag.embedder import TextEmbedding3Small
from core.rag.dbhandler.memgraph import MemGraphClient

import asyncio
import os

#################################################

from core import pretty_print
from datetime import date
from core.llm.chat import Chat

# Initialize the Chat client
chat = Chat.create()

# Define enhanced system role with instructions on using all available tools
system_role = f"""
You are a helpful assistant. 
Your Name is Agent Smith.

Today is {date.today().strftime("%d %B %Y")}.
"""

messages = [{"role": "system", "content": system_role}]

async def run_conversation(user_prompt: str, rag_prompt = None) -> str:
    if rag_prompt:
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
    host="localhost" or os.environ.get("MEMGRAPH_URI", "localhost"),
    port=int(os.environ.get("MEMGRAPH_PORT", 7687)),
    username=os.environ.get("MEMGRAPH_USERNAME", "memgraph"),
    password=os.environ.get("MEMGRAPH_PASSWORD", "memgraph"),
).connect()

embedder = TextEmbedding3Small()

async def test_vector_search(query_text: str):
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

    data = []
    for result in search_results:
        chunk = result["chunk"]
        print(f"Found chunk: {chunk["id"]} with score: {result["similarity"]:.4f}")
        source = db.get_source_by_chunk(chunk["id"])
        print(f"Source: {source['name']} ({source['uri']})")

        data.append({
            "source": source["uri"],
            "content": chunk["content"]
        })

    rag_prompt = f"""
You are an expert on everything GitHub.
You have information in the following format of JSON:
[
    {{
        "source": <source URI>,
        "content": <content that is grounded in the sources>
    }}
]
You always HAVE TO ground your response in this information.
You always have to include Links to relevant information if you have them.
You always HAVE TO include the source, where the information is coming from when you give an answer.

If you don't know the answer, say "I don't know".
Here is the information You have:\n
    """

    import json
    await run_conversation(query_text, f"{rag_prompt}{json.dumps(data)}")


async def main():
    text = input("Enter your text: ")
    #text = "What user data is collected when interacting with Gemini, Claude and OpenAI Models? And for how long is this data retained?"
    await test_vector_search(text)
    #await run_conversation(text)
    print("Test completed.")

if __name__ == "__main__":
    asyncio.run(main())