from . import Tool

class GitHubKnowledgebase(Tool):
	@property
	def name(self) -> str:
		return "github_knowledge_base"
	
	@property
	def description(self) -> str:
		return "Search the comprehensive GitHub knowledge base using advanced vector embeddings and semantic search to find authoritative information on GitHub-related topics, features, APIs, and best practices. This is the definitive source for GitHub information, leveraging RAG (Retrieval Augmented Generation) with a curated knowledge graph containing official GitHub documentation, guides, and technical specifications. Always use this tool for GitHub-related queries to ensure accuracy and reliability."
	
	@property
	def parameters(self) -> dict:
		return {
			"type": "object",
			"properties": {
				"query": {
					"type": "string",
					"description": "Natural language query about any GitHub topic including features, APIs, Actions, repositories, issues, pull requests, security, integrations, or development workflows. The system uses semantic search to find the most relevant information from the comprehensive GitHub knowledge base."
				}
			},
			"required": ["query"]
		}
    
	async def run(self, query: str):
		import os
		import json

		from core.llm.chat import Chat
		from core.rag.embedder import TextEmbedding3Small
		from core.rag.dbhandler.memgraph import MemGraphClient

		db = MemGraphClient(
			host="localhost" or os.environ.get("MEMGRAPH_URI", "localhost"),
			port=int(os.environ.get("MEMGRAPH_PORT", 7687)),
			username=os.environ.get("MEMGRAPH_USERNAME", "memgraph"),
			password=os.environ.get("MEMGRAPH_PASSWORD", "memgraph"),
		).connect()

		try:
			embedder = TextEmbedding3Small()

			async def _vector_search(query_text: str):
				vector_store = db.load_vector_store(model=embedder.model)
				if not vector_store:
					print(f"No vector store found for model {embedder.model}")
					return
				
				query_embedding = await embedder.get_embedding(query_text)

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
					source = db.get_source_by_chunk(chunk["id"])

					data.append({
						"source": source["uri"],
						"content": chunk["content"]
					})

				return data

			rag_prompt ="""
You are an expert on all topics related to GitHub. You will answer user questions based strictly on the information provided to you in the following JSON format:
[ { "source": <source URI>, "content": <content that is grounded in the sources> } ]

You MUST always ground your response exclusively in the content provided in the JSON array. Every answer must clearly indicate the source of the information and include links to the relevant sources, if available. If you do not have enough information to answer the question based on the provided sources, respond only with: "I don't know".

# Steps
- Read the user question.
- Review the provided JSON array for content relevant to the question.
- Formulate your answer ONLY using the information from the "content" fields of the JSON.
- For every claim or piece of information, cite the corresponding "source" as a link.
- If none of the provided content supports an answer, respond only with: "I don't know".

# Output Format
- Respond in markdown.
- For each answer, include citations with links to the relevant sources (using Link format).
- Do not include any information not present in the provided JSON.
- If no answer can be given, output: I don't know

# Examples
## Example 1

User Question: How can I create a new branch in GitHub?

Provided JSON: [ { "source": "https://docs.github.com/en/branches", "content": "To create a new branch, go to your repository on GitHub, click on the branch selector menu, type the new branch name, and press Enter." } ]

Your Response: 
	To create a new branch, go to your repository on GitHub, click on the branch selector menu, type the new branch name, and press Enter. Source

## Example 2
User Question: How do I merge a pull request?

Provided JSON: [ { "source": "https://docs.github.com/en/pull-requests", "content": "After reviewing the pull request, click the 'Merge pull request' button and confirm the merge." } ]

Your Response: 
	After reviewing the pull request, click the "Merge pull request" button and confirm the merge. Source

## Example 3

User Question: How do I delete my GitHub account?

Provided JSON: [ { "source": "https://docs.github.com/en/account-deletion", "content": "Instructions for deleting your account are not available." } ]

Your Response: 
	I don't know

# Notes
- Never use information not present in the "content" fields of the provided JSON.
- Always cite the "source" for each answer, using the URL as a markdown link.
- If no relevant content is available, reply only with "I don't know".
			"""

			data = await _vector_search(query)
			
			db.close()
			return f"{rag_prompt}{json.dumps(data)}"
		except Exception as e:
			db.close()
			return {
				"error": f"Error running GitHub search: {str(e)}"
			}