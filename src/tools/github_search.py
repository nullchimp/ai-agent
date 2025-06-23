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
				Here is the information You know:\n
			"""

			data = await _vector_search(query)
			
			db.close()
			return f"{rag_prompt}{json.dumps(data)}"
		except Exception as e:
			db.close()
			return {
				"error": f"Error running GitHub search: {str(e)}"
			}