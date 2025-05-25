# Architectural Decision Record: Retrieval-Augmented Generation (RAG) with Graph Database for Knowledge Storage

## Context

The AI Agent previously answered queries by sending the full chat history to Azure OpenAI, which had several limitations:

* **No Knowledge Persistence**: Conversations were ephemeral with no information retained across sessions
* **Limited Context Size**: Token limits restricted the amount of conversation history
* **Knowledge Cutoff**: LLMs could only answer based on their training data cutoff point
* **No Relationship Modeling**: Simple vector stores couldn't model complex knowledge relationships

Implementing a RAG system with a graph database addresses these limitations by providing:

* **Persistent Knowledge Store**: Documents and their relationships are preserved
* **Semantic Search**: Vector embeddings enable finding relevant information regardless of phrasing
* **Knowledge Relationships**: Graph structure captures connections between information pieces
* **Extendable Schema**: The model can evolve to support new entity and relationship types

## Decision

1. **Implementation Structure**
   
   Created a modular implementation across `src/core/rag/` and `src/libs/dataloader/` with these components:

   ```
   src/core/rag/
   ├── schema.py           # Node and edge type definitions
   ├── dbhandler/          # Database interface implementations
   │   ├── __init__.py     # MemgraphClient implementation
   │   └── memgraph.py     # Memgraph-specific operations
   └── embedder/           # Vector embedding generation
       ├── __init__.py     # Base embedding service
       └── text_embedding_3_small.py  # Azure OpenAI embedding

   src/libs/dataloader/    # Content loading mechanisms
   ├── __init__.py         # Base loader class
   ├── document.py         # File-based document loader
   └── web.py              # Web content loader
   ```

2. **Data Model and Schema**

   The implementation uses these core node types:

   ```
   (:Source {id, name, type, uri})  # Origin of documents
   (:Document {id, path, content, title, source_id})  # Full documents
   (:DocumentChunk {id, path, content, parent_id, chunk_index})  # Document portions
   (:VectorStore {id, model, status})  # Vector embedding configuration
   (:Vector {id, chunk_id, vector_store_id, embedding})  # Actual embeddings
   (:Interaction {id, session_id, content, role})  # Chat messages
   ```

   Connected by these relationships:

   ```
   (:Document)-[:SOURCED_FROM]->(:Source)  # Document origin
   (:DocumentChunk)-[:CHUNK_OF]->(:Document)  # Document hierarchy
   (:Vector)-[:EMBEDDING_OF]->(:DocumentChunk)  # Link vectors to content
   (:Vector)-[:STORED_IN]->(:VectorStore)  # Vector configuration
   (:Interaction)-[:FOLLOWS]->(:Interaction)  # Message sequence
   (:Document)-[:REFERENCES]->(:Source)  # External references
   ```

3. **Content Embedding Pipeline**

   The system processes content through this workflow:

   1. **Content Loading**: Files or web pages are loaded via specialized loaders
   2. **Text Splitting**: Content is divided into semantic chunks with overlap
   3. **Embedding Generation**: Chunks are converted to vector embeddings
   4. **Graph Storage**: Content and embeddings are stored with relationships

4. **Vector Search Capabilities**

   The implementation supports:
   
   * **Vector Similarity Search**: `search_chunks()` finds relevant content
   * **Batch Processing**: `process_chunks()` handles multiple chunks efficiently
   * **Configurable Parameters**: Customizable chunk size, overlap, vector dimensions

5. **Memgraph Integration**

   Chose Memgraph as the graph database because it offers:
   
   * Vector search capabilities with various distance metrics (cosine, euclidean)
   * Cypher query language for relationship traversal
   * Open-source availability with containerized deployment option

## Consequences

### Positive
+ ✅ **Enhanced Retrieval**: The system can find relevant information based on semantic similarity
+ ✅ **Persistent Knowledge**: Documents and their relationships are preserved across sessions
+ ✅ **Separation of Concerns**: Modular design allows for swapping components (loaders, embedders)
+ ✅ **Flexible Content Sources**: Support for both file-based and web-based content
+ ✅ **Batch Processing**: Efficient handling of multiple documents and chunks

### Negative
- ❌ **Increased Complexity**: More components to maintain and coordinate
- ❌ **Infrastructure Requirements**: Requires running Memgraph database
- ❌ **Storage Overhead**: Storing both content and embeddings increases storage needs
- ❌ **Environment Dependencies**: Relies on Azure OpenAI API for embeddings

## Technical Implementation Details

### Core Components

1. **Graph Client**
   ```python
   class MemGraphClient:
       def __init__(
           self,
           host: str = "127.0.0.1",
           port: int = 7687,
           username: str | None = None,
           password: str | None = None,
       )
   ```

2. **Schema Definition**
   ```python
   class EdgeType(Enum):
       CHUNK_OF = "CHUNK_OF"          # DocumentChunk ➜ Document
       FOLLOWS = "FOLLOWS"            # Interaction ➜ Interaction
       SOURCED_FROM = "SOURCED_FROM"  # Document ➜ Source
       STORED_IN = "STORED_IN"        # Vector ➜ VectorStore
       EMBEDDING_OF = "EMBEDDING_OF"  # Vector ➜ DocumentChunk
       REFERENCES = "REFERENCES"      # Document ➜ Source
   ```

3. **Content Loading**
   ```python
   class WebLoader(Loader):
       def __init__(self, 
                   url: str, 
                   url_pattern: Optional[str] = None, 
                   max_urls: int = 10000, 
                   chunk_size: int = 1024, 
                   chunk_overlap: int = 200)
   ```

4. **Embedding Service**
   ```python
   class TextEmbedding3Small(EmbeddingService):
       @property
       def model(self) -> str:
           return "text-embedding-3-small"
   ```

5. **Vector Search**
   ```python
   def search_chunks(
       self,
       query_vector: Sequence[float],
       k: int = 5,
       index_name: str = "vector_embedding_index"
   ) -> List[Dict[str, Any]]
   ```

### Environment Configuration

The implementation relies on these environment variables:

```
AZURE_OPENAI_API_KEY: For embedding generation
MEMGRAPH_URI: Graph database location (default: localhost)
MEMGRAPH_PORT: Database port (default: 7687)
MEMGRAPH_USERNAME: Database credentials (default: memgraph)
MEMGRAPH_PASSWORD: Database credentials (default: memgraph)
```

## Alternatives Considered

1. **Pure Vector Database**: Considered using Pinecone or similar, but would lack relationship modeling
2. **Traditional Document Database**: MongoDB or similar would lack vector similarity search
3. **Using LlamaIndex directly**: Would provide many features but with less control over the implementation
4. **Neo4j instead of Memgraph**: Neo4j has more mature ecosystem but Memgraph offered better vector operations

## Future Enhancements

1. **Conversation Context Integration**
   - Track chat history in the graph
   - Connect user messages to relevant document chunks
   - Enable conversation-aware document retrieval

2. **Knowledge Graph Enrichment**
   - Extract concepts and entities from documents
   - Build relationships between related concepts
   - Enable traversal-based knowledge discovery

3. **Relevance Feedback**
   - Track which documents were helpful for which queries
   - Improve ranking based on feedback
   - Implement personalized document ranking

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
    parent_id: str
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