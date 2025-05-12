# Architectural Decision Record: Integrate Retrieval-Augmented Generation (RAG) via Graph Database

## Context
The AI Agent currently answers queries by forwarding the full chat history to Azure OpenAI.  
Limitations:

* **Knowledge horizon** – the LLM can only answer from its training cutoff.
* **Grounding** – answers lack citations to internal data sources.
* **Cost & latency** – large prompts increase token usage.

Retrieval-Augmented Generation (RAG) mitigates these issues by fetching relevant, up-to-date context and injecting it into the prompt.  
A **graph database** (e.g. Neo4j, Memgraph) is preferred over a vector store alone because:

* Relationships between entities (files, URLs, MCP tools, prior conversations) are first-class.
* Cypher/Gremlin queries enable complex traversals (e.g. "docs linked to a failing test that touches module X").
* Graph embeddings can still be stored as node/edge properties for semantic search.

## Decision
1. **Add `src/rag/` domain**  
```
src/rag/
├── graph_client.py      # thin wrapper around Neo4j Python driver
├── indexer.py           # parses artifacts -> nodes/edges -> embeddings
├── retriever.py         # Cypher + vector search helpers
└── prompt_builder.py    # injects retrieved context into chat prompt
```
2. **Embed & store artifacts**  
* `tests/`, `docs/`, `src/` files and MCP server metadata are ingested.  
* Each artifact => `Document` node with properties:
```
{id, path, content, embedding: List[float], updated_at}
```
* Edges model:
```
(:Document)-[:REFERS_TO]->(:Symbol)
(:Document)-[:LINKS_TO]->(:URL)
(:Tool)-[:DEFINED_IN]->(:Document)
```
3. **Run-time retrieval flow**  
a. [`rag.retriever.Retriever`](src/rag/retriever.py) receives the user query.  
b. Generates embedding with Azure OpenAI `text-embedding-ada-002`.  
c. Cypher query returns top-K documents by:
```
ORDER BY cosineSimilarity(d.embedding, $queryEmb) DESC, tfidfScore DESC
```  
d. `prompt_builder.build(messages, docs)` creates a new assistant system message:  
```
{"role":"system","content":"Context:\n<doc snippets here>\n---"}
```  
4. **Agent integration**  
* In [`agent.run_conversation`](src/agent.py) insert:
```
docs = retriever.retrieve(query)
messages.insert(1, prompt_builder.build(docs))
```
* Expose CLI flag: `python -m src.agent --rag` toggles RAG.

5. **Deployment & CI**  
* Neo4j spun up via Docker in `docker-compose.yml`; GitHub Actions uses neo4j-official image.  
* `pytest` spins an in-memory Neo4j testcontainer for RAG tests in `tests/rag/`.

## Consequences
+ ✅ Answers grounded with inline citations → higher trust.  
+ ✅ Reduces prompt size to only relevant snippets.  
+ ❌ Adds external dependency (Neo4j) and ingestion pipeline.  
+ ❌ Must secure DB creds (`NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`) via `.env` + GitHub Secrets.

## Alternatives Considered
1. **Pure vector store (FAISS, pgvector)** – simpler but loses graph relations.  
2. **No RAG** – cheaper today; does not scale to proprietary data needs.

## Addressing Open Questions

### 1. Embedding Model Selection

**Decision**: Use Azure OpenAI's `text-embedding-ada-002` as primary embedding model with fallback to `all-MiniLM-L6-v2`.

**Rationale**:
- **Cost-performance balance**: Azure OpenAI's `text-embedding-ada-002` offers high-quality 1536-dimensional embeddings at ~$0.0001/1K tokens, with strong performance-to-cost ratio.
- **Fallback model**: Using Sentence Transformers' `all-MiniLM-L6-v2` as offline fallback provides 384-dimensional embeddings that run locally at zero ongoing cost, with only ~15% quality reduction.
- **Hybrid approach**: Implementation allows configuring which content types use which model (e.g., important code documentation uses OpenAI, test files use MiniLM).

**Implementation**:
```python
class EmbeddingService:
    def __init__(self, openai_client, use_local_fallback=True):
        self.openai_client = openai_client
        self.local_model = None
        if use_local_fallback:
            from sentence_transformers import SentenceTransformer
            self.local_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    async def get_embedding(self, text, use_openai=True):
        if use_openai:
            try:
                result = await self.openai_client.embeddings.create(
                    input=text,
                    model="text-embedding-ada-002"
                )
                return result.data[0].embedding
            except Exception as e:
                if not self.local_model:
                    raise e
                # Fall back to local model
                
        return self.local_model.encode(text).tolist()
```

### 2. Embedding Versioning Strategy

**Decision**: Implement a hash-based versioning system with an incremental update pipeline.

**Rationale**:
- **Avoid redundant processing**: Only regenerate embeddings when content changes.
- **Efficient updates**: Enables incremental updates rather than full reindexing.
- **Change detection**: Ensures embeddings reflect the latest content state.

**Implementation**:
1. **Document versioning schema**:
```
(:Document {
   id: String,
   path: String,
   content: String,
   embedding: List[float],
   content_hash: String,  // SHA-256 hash of content
   embedding_version: String,  // Model version used
   updated_at: DateTime
})
```

2. **Incremental update workflow**:
```python
class DocumentIndexer:
      def __init__(self, graph_client, embedding_service):
         self.graph_client = graph_client
         self.embedding_service = embedding_service
         
      async def index_document(self, path, content):
         # Calculate content hash
         content_hash = hashlib.sha256(content.encode()).hexdigest()
         
         # Check if document exists with same hash
         existing = await self.graph_client.find_document(path)
         if existing and existing.get("content_hash") == content_hash:
            return False  # No changes needed
            
         # Generate new embedding
         embedding = await self.embedding_service.get_embedding(content)
         
         # Store document with updated hash and embedding
         await self.graph_client.upsert_document(
            path=path,
            content=content,
            embedding=embedding,
            content_hash=content_hash,
            embedding_version="text-embedding-ada-002-v1",
            updated_at=datetime.now().isoformat()
         )
         return True
```

3. **CI pipeline integration**:
- GitHub Action that runs on PR merge to detect changed files.
- Only processes files that have changed, avoiding full reindex.
   
4. **Manual full rebuild command**:
```bash
python -m src.rag.tools reindex --model-version=newversion
```

### 3. Confidence Score Surfacing

**Decision**: Implement multi-level confidence scoring with inline citation references.

**Rationale**:
- **Transparent trustworthiness**: Users can assess reliability of answers.
- **Citation traceability**: Clear linkage between statements and sources.
- **Variable confidence handling**: Different strategies for high vs. low confidence information.

**Implementation**:

1. **Citation format in responses**:
```
The module uses asynchronous I/O for database interactions[1,3] and implements connection pooling[2].

References:
[1] src/db/client.py:45-52 (95% match)
[2] docs/design/database.md:120-138 (87% match)
[3] tests/db/test_async_client.py:25-40 (76% match)
```

2. **Confidence calculation**:
- Semantic similarity between query and retrieved passages
- Document recency/freshness
- Citation count across corpus
- LLM self-reported confidence

3. **Prompt enhancement**:
```python
def build_augmented_prompt(query, documents, messages):
      # Sort documents by confidence score
      docs_with_scores = [(doc, calculate_confidence(query, doc)) 
                        for doc in documents]
      docs_with_scores.sort(key=lambda x: x[1], reverse=True)
      
      # Build context section with confidence indicators
      context = "I'll answer based on these sources:\n"
      for i, (doc, score) in enumerate(docs_with_scores):
         context += f"[{i+1}] {doc['path']} (confidence: {score:.0%})\n"
         context += f"```\n{doc['content']}\n```\n\n"
      
      # Enhance prompt with instructions for citation
      system_msg = {
         "role": "system",
         "content": f"{context}\n---\n" +
                  "When answering, cite specific sources using [n] notation. " +
                  "If confidence < 70%, explicitly state limitations of your answer."
      }
      
      # Insert augmented system message
      augmented_messages = messages.copy()
      augmented_messages.insert(1, system_msg)
      return augmented_messages
```

4. **User Interface Integration**:
- Add visual confidence indicators in the UI response
- Let users expand citation references to see full context
- Include a toggle to show/hide confidence metrics

## Technical Implementation Details

### Neo4j Configuration

For optimal performance with embedding-based retrieval in Neo4j:

1. **Index Creation**:
```cypher
CREATE VECTOR INDEX document_embedding IF NOT EXISTS
FOR (d:Document)
ON d.embedding
OPTIONS {indexConfig: {
   `vector.dimensions`: 1536,
   `vector.similarity_function`: 'cosine'
}}
```

2. **Configuration in `neo4j.conf`**:
```
dbms.memory.heap.initial_size=2G
dbms.memory.heap.max_size=4G
dbms.memory.pagecache.size=4G
```

3. **Connection Pooling**:
```python
from neo4j import AsyncGraphDatabase

class Neo4jClient:
      def __init__(self, uri, username, password, max_connection_pool_size=50):
         self.driver = AsyncGraphDatabase.driver(
            uri, 
            auth=(username, password),
            max_connection_pool_size=max_connection_pool_size
         )
```

### Deployment Recommendations

1. **Docker Compose**:
```yaml
version: '3'
services:
   neo4j:
      image: neo4j:5.11.0
      environment:
      - NEO4J_AUTH=neo4j/securepassword
      - NEO4J_apoc_export_file_enabled=true
      - NEO4J_apoc_import_file_enabled=true
      - NEO4J_dbms_security_procedures_unrestricted=apoc.*,algo.*
      ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
      volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
      - neo4j_import:/import
      - neo4j_plugins:/plugins
volumes:
   neo4j_data:
   neo4j_logs:
   neo4j_import:
   neo4j_plugins:
```

2. **Monitoring**:
- Prometheus metrics via Neo4j Metrics plugin
- Grafana dashboard for visual monitoring
- Healthcheck endpoint in the application:
```python
@app.get("/health/neo4j")
async def neo4j_health():
   try:
         result = await graph_client.run_query("RETURN 1 as n")
         return {"status": "healthy", "message": "Neo4j connection successful"}
   except Exception as e:
         return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "message": str(e)}
         )
```

## Next Steps

1. Implement the `src/rag` module with the design patterns described above
2. Create initial test fixtures for validating Neo4j integration
3. Extend the agent CLI with RAG-specific flags
4. Develop pipeline for initial document ingestion and embeddings generation
5. Conduct performance testing to validate query response times

## References

1. [Neo4j Vector Search Documentation](https://neo4j.com/docs/cypher-manual/current/indexes-for-vector-search/)
2. [Azure OpenAI Embeddings Documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models#embeddings-models)
3. [Sentence Transformers Documentation](https://www.sbert.net/docs/pretrained_models.html)
4. [Python Neo4j Driver Documentation](https://neo4j.com/docs/python-manual/current/)