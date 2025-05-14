# Architectural Decision Record: Integrate Retrieval-Augmented Generation (RAG) via Graph Database for Knowledge Management

## Context
The AI Agent currently answers queries by forwarding the full chat history to Azure OpenAI.  
Limitations:

* **Knowledge persistence** – conversations are ephemeral with no persistent knowledge across sessions.
* **Contextual understanding** – the agent lacks ability to link related information from past interactions.
* **Knowledge horizon** – the LLM can only answer from its training cutoff.
* **Conversational memory** – no mechanism to recall specific prior user interactions.

Retrieval-Augmented Generation (RAG) with a knowledge graph approach mitigates these issues by creating a persistent, traversable store of knowledge and chat history.  
A **graph database** (e.g. Neo4j, Memgraph) is preferred over a vector store alone because:

* **Conversation threading** – allows tracking of complete conversation flows and their relationships.
* **Knowledge evolution** – captures how information changes over time through user interactions.
* **Contextual recall** – enables retrieval based on conversational context, not just content similarity.
* **Multi-hop reasoning** – supports traversing relationships between concepts mentioned across conversations.

## Decision
1. **Implement `src/core/rag/` domain with MemGraphClient**  
```
src/core/rag/
├── graph_client.py      # core wrapper around Neo4j/Memgraph driver
├── document_loader.py   # handles ingestion of various document formats
├── text_splitter.py     # splits documents into overlapping chunks
├── _indexer.py          # ingests artifacts, messages, and conversations
├── retriever.py         # conversation-aware knowledge retrieval
└── memory.py            # manages long-term conversation history
```

2. **Conversation and Knowledge Storage Model**  
* Current implemented schema (from graph_client.py):
```
(:Conversation {id, start_time, title, summary})
(:Message {id, content, role, timestamp})-[:PART_OF]->(:Conversation)
(:Message)-[:REFERENCES]->(:Document)
(:Message)-[:MENTIONS]->(:Concept)
(:Document {id, path, content, embedding, content_hash, embedding_version, updated_at, source_path, title, author, mime_type})
(:DocumentChunk {id, path, content, embedding, content_hash, embedding_version, chunk_index, parent_document_id, updated_at})-[:CHUNK_OF]->(:Document)
(:Resource {uri, type, description})
(:User {id, name})-[:VIEWED]->(:Document)
(:Concept {id, name})
(:Topic {id, name})
(:Symbol {name})
(:Tool {name})-[:DEFINED_IN]->(:Document)
(:Question {id, content, created_at})-[:ANSWERED_BY]->(:Document)
(:Entity {id, name, type})
```

* Relationship types implemented:
```
(:Document)-[:REFERS_TO]->(:Symbol)
(:Document)-[:LINKS_TO]->(:Resource)
(:DocumentChunk)-[:CHUNK_OF]->(:Document)
(:Message)-[:PART_OF]->(:Conversation)
(:Message)-[:REFERENCES]->(:Document)
(:Message)-[:MENTIONS]->(:Concept)
(:Document)-[:BELONGS_TO]->(:Topic)
(:Document)-[:EXPLAINS]->(:Concept)
(:Concept)-[:RELATED_TO]->(:Concept)
(:User)-[:VIEWED]->(:Document)
(:Question)-[:ANSWERED_BY]->(:Document)
(:Document)-[:REFERENCES]->(:Document)
(:Document)-[:REFERENCES]->(:Resource)
```

3. **Enhanced Chat History Management**
* Implemented conversation storage with metadata:
```
(:Conversation {
   id: UUID,
   start_time: DateTime,
   title: String,
   summary: String        // AI-generated summary of conversation topic
})

(:Message {
   id: UUID,
   content: String,
   role: String,         // "user" or "assistant"
   timestamp: DateTime
})-[:PART_OF]->(:Conversation)

// Message references to documents and concepts
(:Message)-[:REFERENCES]->(:Document)
(:Message)-[:MENTIONS]->(:Concept)
```

4. **Vector-Based Semantic Search**
* The implementation uses vector embeddings for document search with fallback mechanisms:
  * Primary: `semantic_search()` using Memgraph's vector operations with cosine similarity
  * Fallback: `semantic_search_fallback()` with client-side vector similarity computation
  * Enhanced: `conversation_aware_search()` that combines document and conversation search

5. **Privacy and Retention Management**
* Conversation management with features for data lifecycle:
  * `get_expired_conversations()`: Find conversations older than retention period (default 90 days)
  * `delete_conversation()`: Remove conversations and orphaned messages
  * Future enhancement: Implement anonymization for sensitive information

6. **Agent Integration**  
* The graph client provides methods for integrating with the main agent:
```python
# Example integration flow:
# 1. Create or continue conversation
conversation_id = await graph_client.create_conversation()

# 2. Store each message in the conversation
message_id = await graph_client.add_message(
    conversation_id=conversation_id,
    content=user_message,
    role="user",
    timestamp=datetime.now()
)

# 3. Get relevant knowledge
query_embedding = await embedding_service.get_embedding(user_query)
knowledge = await graph_client.conversation_aware_search(
    query_embedding=query_embedding,
    conversation_id=conversation_id
)

# 4. Store assistant's response
await graph_client.add_message(
    conversation_id=conversation_id,
    content=response.content,
    role="assistant",
    timestamp=datetime.now(),
    references=[doc["path"] for doc in knowledge]
)
```

7. **Knowledge Organization Features**
* Document categorization:
  * `link_document_to_topic()` - Associate documents with topics
  * `link_document_explains_concept()` - Create knowledge relationships
  * `create_document_reference()` - Create document cross-references

* User knowledge tracking:
  * `track_user_viewed_document()` - Record user document interactions
  * `create_or_get_user()` - Manage user identities

## Consequences
+ ✅ **Persistent knowledge** - Agent learns and improves from each user interaction.  
+ ✅ **Conversation memory** - Agent can recall specific past interactions with users.
+ ✅ **Knowledge association** - Related information links automatically across conversations.
+ ✅ **Cross-session continuity** - Users can continue conversations across sessions.
+ ✅ **Fallback mechanisms** - Robust search with client-side calculation when needed.
+ ✅ **Unified resource model** - Single Resource node type represents all external references.
+ ❌ Increased complexity and storage requirements.
+ ❌ Higher computational overhead for knowledge extraction and management.
+ ❌ Security considerations for `MEMGRAPH_URI`, `MEMGRAPH_USERNAME`, `MEMGRAPH_PASSWORD` via `.env`.

## Alternatives Considered
1. **Session-based memory only** - Simpler but lacks persistence and cross-session knowledge.
2. **Document-oriented storage** - Easier to implement but lacks relationship modeling.
3. **Pure vector store** - More efficient for similarity search but cannot model complex conversation relationships.
4. **Separate URL and Source nodes** - Earlier implementation had distinct nodes for web links and file sources.

## Technical Implementation Details

### Core Features Implemented

1. **Document Management**
   * `create_document()` - Create document nodes with content and embeddings
   * `upsert_document()` - Update or create documents
   * `find_document()` - Retrieve documents by path
   * `create_document_chunk()` - Create document chunk nodes for fine-grained retrieval
   * `get_document_chunks()` - Retrieve all chunks belonging to a document

2. **Document Processing Pipeline**
   * `DocumentLoader` - Loads various document formats using llama-index readers
   * `TextSplitter` - Splits documents into chunks with configurable overlap
   * `Indexer` - Processes documents, splits into chunks, and stores in graph database

3. **Chunk-Based Search and Retrieval**
   * `semantic_search_chunks()` - Vector-based chunk retrieval
   * `conversation_aware_search_chunks()` - Context-aware chunk retrieval
   * `semantic_search_chunks_fallback()` - Fallback chunk search when vector functions unavailable

4. **Resource Management**
   * `create_resource()` - Create unified resource nodes for external references
   * `link_document_to_resource()` - Connect documents to resources they reference
   * Resource schema:
     ```
     (:Resource {
        uri: String,      // Standardized URI (file://, http://, etc.)
        type: String,     // Resource type: "web", "file", "database", etc.
        description: String  // Optional description
     })
     ```

5. **Relationship Management**
   * `create_symbol()` - Create code symbols from documents
   * `create_url_link()` - Create web resource links (now using Resource nodes)
   * `create_tool()` - Track agent tool definitions

6. **Conversation Management**
   * `create_conversation()` - Start new conversation threads
   * `add_message()` - Record user and assistant messages
   * `get_conversation_messages()` - Retrieve conversation history

7. **Knowledge Organization**
   * `create_or_get_concept()` - Manage domain concepts
   * `create_or_get_topic()` - Organize documents by topic
   * `link_related_concepts()` - Create concept relationships

8. **Search and Retrieval**
   * `semantic_search()` - Vector-based document retrieval
   * `conversation_aware_search()` - Context-aware knowledge retrieval
   * `_cosine_similarity()` - Vector similarity computation

### Connection and Environment Management

1. **Database Connection**
```python
class MemGraphClient:
    def __init__(self, 
                 uri: Optional[str] = None, 
                 username: Optional[str] = None, 
                 password: Optional[str] = None, 
                 max_connection_pool_size: int = 50):
        self.uri = uri or os.environ.get("MEMGRAPH_URI") or "bolt://localhost:7687"
        self.username = username or os.environ.get("MEMGRAPH_USERNAME") or "neo4j"
        self.password = password or os.environ.get("MEMGRAPH_PASSWORD") or "aiagentpassword"
        
        self.driver = AsyncGraphDatabase.driver(
            self.uri,
            auth=(self.username, self.password),
            max_connection_pool_size=max_connection_pool_size
        )
```

2. **Helper Functions**
```python
def standardize_resource_uri(path: str) -> str:
    """Standardize resource URIs for consistent reference matching"""
    # Convert to absolute path if possible
    if os.path.exists(path):
        path = os.path.abspath(path)
    
    # Normalize path separators
    path = path.replace('\\', '/')
    
    # Determine resource type and format URI appropriately
    if path.startswith(('http://', 'https://')):
        return path  # Already a well-formed web URI
    
    # For file paths, ensure they have a proper file:// scheme if they're absolute
    if os.path.isabs(path):
        if not path.startswith('file://'):
            return f"file://{path}"
    
    return path
```

### Enhanced Document Processing

1. **Document Chunking Strategy**
```python
class TextSplitter:
    def __init__(
        self,
        chunk_size: int = 1024,
        chunk_overlap: int = 200,
        separator: str = "\n"
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separator = separator
```

2. **Document Chunk Structure**
```python
class ChunkMetadata(DocumentMetadata):
    chunk_index: int
    chunk_count: int
    parent_document_id: str
    parent_document_path: str
    is_chunk: bool

class DocumentChunk(Document):
    metadata: ChunkMetadata
```

3. **Multi-Format Document Loading**
   * PDF document loader
   * DOCX document loader
   * Markdown document loader
   * Plain text document loader
   * HTML document loader

### Future Enhancements

1. **Automated Knowledge Extraction**
   * Implement concept extraction from conversations
   * Use LLMs to identify key entities and relationships

2. **Temporal Analysis**
   * Track knowledge evolution over time
   * Identify trends in conversation topics

3. **Advanced Privacy Controls**
   * Implement conversation anonymization
   * Add user-controlled privacy settings

4. **Semantic Chunk-Based Retrieval**
   * Implement hierarchical retrieval (find relevant chunks, then expand to context)
   * Add chunk relationship awareness for improved context retrieval
   * Develop chunk reranking strategies based on conversational context