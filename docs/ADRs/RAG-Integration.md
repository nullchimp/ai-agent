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
1. **Enhance `src/rag/` domain**  
```
src/rag/
├── graph_client.py      # thin wrapper around Neo4j Python driver
├── indexer.py           # ingests artifacts, messages, and conversations
├── retriever.py         # conversation-aware knowledge retrieval
├── prompt_builder.py    # integrates conversational context into prompts
└── memory.py            # manages long-term conversation history
```

2. **Conversation and Knowledge Storage Model**  
* Chat messages, documents, and knowledge entities are all stored in the graph
* Core schema:
```
(:Conversation {id, timestamp, title, summary})
(:Message {id, content, role, timestamp})-[:PART_OF]->(:Conversation)
(:Message)-[:REFERENCES]->(:Document)
(:Message)-[:MENTIONS]->(:Concept)
(:User {id, name})-[:AUTHORED]->(:Message)
(:Document {id, path, content, embedding, updated_at, source_path, mime_type, title, author})
```

* Edges model:
```
// Core knowledge entities
(:Concept)                              // Represents domain concepts, terminologies
(:Topic)                                // Higher-level knowledge categories
(:Document)-[:BELONGS_TO]->(:Topic)     // Document categorization
(:Document)-[:EXPLAINS]->(:Concept)     // Document explains a concept
(:Concept)-[:RELATED_TO]->(:Concept)    // Concept relationships
(:User)-[:VIEWED]->(:Document)          // User interaction tracking
(:Question)-[:ANSWERED_BY]->(:Document) // Question-answer relationships
(:Document)-[:REFERENCES]->(:Document)  // Document reference relationships
(:Document)-[:SOURCED_FROM]->(:Source)  // Document source tracking
```

3. **Enhanced Chat History Management**
* Store complete conversations with metadata:
```
(:Conversation {
   id: UUID,
   start_time: DateTime,
   end_time: DateTime,
   summary: String,        // AI-generated summary of conversation topic
   sentiment: String,      // Overall conversation sentiment
   topic_clusters: List    // Auto-detected topic clusters
})

(:Message {
   id: UUID,
   content: String,
   role: String,           // "user" or "assistant"
   timestamp: DateTime,
   embedding: List[float], // Embedded for semantic search
   sentiment: String,      // Per-message sentiment
   entities: List          // Extracted named entities
})-[:PART_OF]->(:Conversation)

// Explicit connections between related messages
(:Message)-[:REFERENCES]->(:Message)
(:Message)-[:ANSWERS]->(:Message {role: "user"})
```

4. **Knowledge Building from Conversations**
* Extract concepts and facts automatically from conversations:
```python
async def extract_knowledge_from_message(message):
    """Extract knowledge entities and relationships from a message"""
    # Use LLM to identify concepts, facts, and relationships
    extraction_prompt = f"""
    Extract key concepts, entities and factual claims from this message:
    {message.content}
    
    Format as JSON with:
    - concepts: list of domain concepts mentioned
    - entities: specific named entities
    - facts: list of factual claims made
    - relationships: connections between concepts/entities
    """
    
    extraction = await openai_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": extraction_prompt}]
    )
    
    # Parse the extraction results
    data = json.loads(extraction.choices[0].message.content)
    
    # Store in graph database
    for concept in data["concepts"]:
        await graph_client.create_concept(concept["name"])
        await graph_client.link_message_to_concept(message.id, concept["name"])
```

5. **Conversation-Aware Retrieval Flow**  
a. [`rag.retriever.Retriever`](src/rag/retriever.py) receives user query with conversation context.  
b. Generates embedding for query using Azure OpenAI `text-embedding-ada-002`.  
c. Multi-stage retrieval combines:
   * Relevant past conversation segments
   * Related concepts and documents
   * Current conversation context
   
d. Cypher query example for conversation-aware retrieval:
```cypher
// Find relevant past conversations
MATCH (c:Conversation)
WHERE c.id <> $current_conversation_id
WITH c, gds.similarity.cosine(c.embedding, $query_embedding) AS score
WHERE score > 0.7
ORDER BY score DESC
LIMIT 3

// Get messages from those conversations
MATCH (m:Message)-[:PART_OF]->(c) 
WITH m
ORDER BY m.timestamp
// Find documents referenced in those messages
OPTIONAL MATCH (m)-[:REFERENCES]->(d:Document)
RETURN m.content, d.content, score
ORDER BY score DESC
LIMIT 10
```

6. **Agent Integration**  
* In [`agent.run_conversation`](src/agent.py) enhance with:
```python
# Create or continue conversation
conversation_id = conversation_id or graph_client.create_conversation()

# Store each message in the conversation
message_id = await graph_client.add_message(
    conversation_id=conversation_id,
    content=user_message,
    role="user",
    timestamp=datetime.now()
)

# Get relevant knowledge and conversation history
knowledge = await retriever.get_conversation_context(
    query=user_message,
    conversation_id=conversation_id,
    message_id=message_id
)

# Build enhanced prompt with knowledge + chat history
enhanced_messages = prompt_builder.build_with_memory(
    messages=messages,
    knowledge=knowledge,
    conversation_history=graph_client.get_conversation_summary(conversation_id)
)

# Store assistant's response for future context
await graph_client.add_message(
    conversation_id=conversation_id,
    content=response.content,
    role="assistant",
    timestamp=datetime.now(),
    references=knowledge.document_ids  # Link to source documents
)

# Extract and store knowledge from the conversation
await knowledge_extractor.process_message(message_id)
```

* Expose enhanced CLI flags:
  * `--rag` - Enable RAG capabilities
  * `--persist-chat` - Store chat history in knowledge graph
  * `--conversation-id <ID>` - Continue specific conversation

7. **Deployment & Implementation**  
* Neo4j spun up via Docker in `docker-compose.yml` with persistent volume for knowledge retention.
* Daily automated knowledge graph backup to S3/Azure Blob storage.
* Knowledge pruning policies to manage graph size:
  * Conversational turns older than 90 days condensed to summaries
  * Orphaned concepts pruned if no references for 180+ days

## Consequences
+ ✅ **Persistent knowledge** - Agent learns and improves from each user interaction.  
+ ✅ **Conversation memory** - Agent can recall specific past interactions with users.
+ ✅ **Knowledge association** - Related information links automatically across conversations.
+ ✅ **Cross-session continuity** - Users can continue conversations across sessions.
+ ❌ Increased complexity and storage requirements.
+ ❌ Higher computational overhead for knowledge extraction and management.
+ ❌ Must secure sensitive conversation data (`NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`) via `.env` + GitHub Secrets.

## Alternatives Considered
1. **Session-based memory only** - Simpler but lacks persistence and cross-session knowledge.
2. **Document-oriented storage** - Easier to implement but lacks relationship modeling.
3. **Pure vector store** - More efficient for similarity search but cannot model complex conversation relationships.

## Addressing Open Questions

### 1. Embedding Model Selection

**Decision**: Use Azure OpenAI's `text-embedding-ada-002` as primary embedding model with fallback to `all-MiniLM-L6-v2`.

**Rationale**:
- **Conversation embedding quality** - Azure OpenAI's model better captures nuanced conversational context.
- **Cost-performance balance**: Azure OpenAI's `text-embedding-ada-002` offers high-quality 1536-dimensional embeddings at ~$0.0001/1K tokens, with strong performance-to-cost ratio.
- **Fallback model**: Using Sentence Transformers' `all-MiniLM-L6-v2` as offline fallback provides 384-dimensional embeddings that run locally at zero ongoing cost.

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

### 2. Conversation Indexing Strategy

**Decision**: Implement a hierarchical conversation indexing approach with automatic topic clustering.

**Rationale**:
- **Efficient retrieval** - Group related conversations by topic clusters.
- **Temporal organization** - Capture conversation flow and evolution over time.
- **Scalable design** - Support thousands of conversations without performance degradation.

**Implementation**:
1. **Conversation Topic Clustering**:
```python
async def create_conversation_clustering(conversations, num_clusters=10):
    """Group conversations into topic clusters"""
    # Extract embeddings from conversation summaries
    embeddings = [conv.summary_embedding for conv in conversations]
    
    # Use scikit-learn for clustering
    from sklearn.cluster import KMeans
    kmeans = KMeans(n_clusters=num_clusters)
    clusters = kmeans.fit_predict(embeddings)
    
    # Update conversation nodes with cluster assignments
    for i, conversation in enumerate(conversations):
        await graph_client.update_conversation(
            id=conversation.id,
            properties={"topic_cluster": int(clusters[i])}
        )
    
    # Create TopicCluster nodes
    for cluster_id in range(num_clusters):
        # Get conversations in this cluster
        cluster_convs = [conv for i, conv in enumerate(conversations) 
                       if clusters[i] == cluster_id]
        
        # Extract key terms from the cluster
        terms = extract_key_terms(cluster_convs)
        
        await graph_client.create_topic_cluster(
            id=cluster_id,
            name=f"Topic {cluster_id}",
            key_terms=terms,
            conversation_ids=[c.id for c in cluster_convs]
        )
```

2. **Conversation Summary Generation**:
```python
async def generate_conversation_summary(conversation_id):
    """Generate a concise summary of a conversation"""
    # Get all messages in the conversation
    messages = await graph_client.get_conversation_messages(conversation_id)
    
    # Combine messages into a transcript
    transcript = "\n".join([f"{m.role}: {m.content}" for m in messages])
    
    # Generate summary using OpenAI
    summary_response = await openai_client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Summarize this conversation in 2-3 sentences."},
            {"role": "user", "content": transcript}
        ]
    )
    
    summary = summary_response.choices[0].message.content
    
    # Generate embedding for the summary
    summary_embedding = await embedding_service.get_embedding(summary)
    
    # Store the summary
    await graph_client.update_conversation(
        id=conversation_id,
        properties={
            "summary": summary,
            "summary_embedding": summary_embedding
        }
    )
    
    return summary
```

### 3. Privacy and Data Management

**Decision**: Implement a comprehensive privacy system for conversation data.

**Rationale**:
- **User trust** - Clear control over personal conversation data.
- **Compliance** - Support for data privacy regulations.
- **Data lifecycle** - Proper management of conversational data over time.

**Implementation**:

1. **Privacy Controls**:
```python
class ConversationPrivacyManager:
    async def set_conversation_privacy(self, conversation_id, settings):
        """
        Set privacy controls for a conversation
        settings = {
            "retention_days": int,  # Days to keep the full conversation
            "anonymize": bool,      # Whether to anonymize personal info
            "accessibility": str    # "private", "shared", or "public"
        }
        """
        await graph_client.update_conversation(
            id=conversation_id,
            properties={
                "privacy_settings": settings,
                "expiration_date": datetime.now() + 
                                  timedelta(days=settings["retention_days"])
            }
        )
    
    async def anonymize_conversation(self, conversation_id):
        """Replace personally identifiable information with placeholders"""
        messages = await graph_client.get_conversation_messages(conversation_id)
        
        for message in messages:
            # Use NER to identify personal information
            anonymized = await self._anonymize_text(message.content)
            await graph_client.update_message(
                id=message.id,
                properties={"content": anonymized, "anonymized": True}
            )
    
    async def enforce_retention_policy(self):
        """Apply retention policies to expired conversations"""
        expired = await graph_client.get_expired_conversations()
        for conversation in expired:
            if conversation.privacy_settings.get("anonymize"):
                await self.anonymize_conversation(conversation.id)
            else:
                await graph_client.delete_conversation(conversation.id)
```

## Technical Implementation Details

### Neo4j Configuration for Conversation Management

For optimal performance with conversation management and knowledge graph:

1. **Index Creation**:
```cypher
// Vector index for message content search
CREATE VECTOR INDEX message_embedding IF NOT EXISTS
FOR (m:Message)
ON m.embedding
OPTIONS {indexConfig: {
   `vector.dimensions`: 1536,
   `vector.similarity_function`: 'cosine'
}}

// Text index for conversation search
CREATE TEXT INDEX conversation_summary IF NOT EXISTS
FOR (c:Conversation)
ON c.summary
```

2. **Configuration in `neo4j.conf`**:
```
dbms.memory.heap.initial_size=4G
dbms.memory.heap.max_size=8G
dbms.memory.pagecache.size=8G
```

3. **Conversation-optimized connection pooling**:
```python
from neo4j import AsyncGraphDatabase

class ConversationGraphClient:
    def __init__(self, uri, username, password, max_connection_pool_size=100):
        self.driver = AsyncGraphDatabase.driver(
            uri, 
            auth=(username, password),
            max_connection_pool_size=max_connection_pool_size
        )
        
    async def create_conversation(self, title=None):
        """Create a new conversation node"""
        query = """
        CREATE (c:Conversation {
            id: randomUUID(),
            start_time: datetime(),
            title: $title
        })
        RETURN c.id as id
        """
        result = await self.driver.execute_query(
            query,
            {"title": title or "New Conversation"}
        )
        return result[0]["id"]
```

### Knowledge Extraction System

1. **Entity and Concept Extraction**:
```python
class KnowledgeExtractor:
    def __init__(self, openai_client, graph_client):
        self.openai_client = openai_client
        self.graph_client = graph_client
        
    async def extract_from_message(self, message_id):
        """Extract knowledge from a message"""
        message = await self.graph_client.get_message(message_id)
        
        # Extract entities and concepts
        extraction = await self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Extract entities and concepts from this message."},
                {"role": "user", "content": message.content}
            ],
            response_format={"type": "json_object"}
        )
        
        data = json.loads(extraction.choices[0].message.content)
        
        # Store concepts
        for concept in data.get("concepts", []):
            concept_id = await self.graph_client.create_or_get_concept(concept["name"])
            await self.graph_client.create_relationship(
                from_id=message_id, 
                to_id=concept_id,
                relationship_type="MENTIONS"
            )
            
        # Store entities
        for entity in data.get("entities", []):
            entity_id = await self.graph_client.create_or_get_entity(
                entity["name"],
                entity["type"]
            )
            await self.graph_client.create_relationship(
                from_id=message_id,
                to_id=entity_id,
                relationship_type="REFERENCES"
            )
```

### Reference Querying System

1. **Document Reference Retrieval**:
```python
class ReferenceRetriever:
    def __init__(self, graph_client):
        self.graph_client = graph_client
        
    async def get_document_references(self, document_id):
        """Get all references for a specific document"""
        query = """
        MATCH (d:Document {id: $document_id})-[:REFERENCES]->(ref:Document)
        RETURN ref.id as id, ref.title as title, ref.source_path as source_path, 
               ref.author as author, ref.updated_at as updated_at
        """
        results = await self.graph_client.execute_query(query, {"document_id": document_id})
        return [dict(record) for record in results]
    
    async def get_documents_by_source_path(self, source_path_pattern):
        """Find documents by source path pattern"""
        query = """
        MATCH (d:Document)
        WHERE d.source_path =~ $source_path_pattern
        RETURN d.id as id, d.title as title, d.source_path as source_path, 
               d.author as author, d.updated_at as updated_at
        """
        results = await self.graph_client.execute_query(
            query, 
            {"source_path_pattern": source_path_pattern}
        )
        return [dict(record) for record in results]
    
    async def get_references_in_conversation(self, conversation_id):
        """Get all document references mentioned in a conversation"""
        query = """
        MATCH (c:Conversation {id: $conversation_id})
        MATCH (m:Message)-[:PART_OF]->(c)
        MATCH (m)-[:REFERENCES]->(d:Document)
        RETURN DISTINCT d.id as id, d.title as title, d.source_path as source_path, 
                       d.author as author, d.updated_at as updated_at
        """
        results = await self.graph_client.execute_query(query, {"conversation_id": conversation_id})
        return [dict(record) for record in results]
```

2. **Document Ingestion with Source Path**:
```python
class DocumentIngester:
    def __init__(self, graph_client, embedding_service):
        self.graph_client = graph_client
        self.embedding_service = embedding_service
    
    async def ingest_document(self, content, source_path, title=None, author=None, mime_type=None):
        """Ingest a document with source path tracking"""
        # Generate embedding
        embedding = await self.embedding_service.get_embedding(content)
        
        # Create document node
        query = """
        CREATE (d:Document {
            id: randomUUID(),
            content: $content,
            source_path: $source_path,
            title: $title,
            author: $author,
            mime_type: $mime_type,
            embedding: $embedding,
            updated_at: datetime()
        })
        RETURN d.id as id
        """
        
        result = await self.graph_client.execute_query(
            query,
            {
                "content": content,
                "source_path": source_path,
                "title": title or os.path.basename(source_path),
                "author": author,
                "mime_type": mime_type,
                "embedding": embedding
            }
        )
        
        document_id = result[0]["id"]
        
        # Create source node if needed and link document
        source_query = """
        MERGE (s:Source {path: $source_path})
        WITH s
        MATCH (d:Document {id: $document_id})
        CREATE (d)-[:SOURCED_FROM]->(s)
        """
        
        await self.graph_client.execute_query(
            source_query,
            {"source_path": source_path, "document_id": document_id}
        )
        
        return document_id
```

3. **Citation and Reference Management**:
```python
class ReferenceManager:
    def __init__(self, graph_client):
        self.graph_client = graph_client
    
    async def create_document_reference(self, from_document_id, to_document_id, reference_type="REFERENCES", context=None):
        """Create a reference relationship between documents"""
        query = """
        MATCH (d1:Document {id: $from_id})
        MATCH (d2:Document {id: $to_id})
        CREATE (d1)-[:REFERENCES {type: $reference_type, context: $context, created_at: datetime()}]->(d2)
        """
        
        await self.graph_client.execute_query(
            query,
            {
                "from_id": from_document_id,
                "to_id": to_document_id,
                "reference_type": reference_type,
                "context": context
            }
        )
    
    async def get_citation_graph(self, document_id, depth=2):
        """Get the citation graph for a document (both citing and cited-by)"""
        query = """
        MATCH (d:Document {id: $document_id})
        CALL {
            MATCH (d)-[:REFERENCES*1..%d]->(cited:Document)
            RETURN cited as other_doc, "citing" as direction, reduce(depth = 0, r IN relationships() | depth + 1) as depth
            UNION
            MATCH (citing:Document)-[:REFERENCES*1..%d]->(d)
            RETURN citing as other_doc, "cited_by" as direction, reduce(depth = 0, r IN relationships() | depth + 1) as depth
        }
        RETURN other_doc.id as id, other_doc.title as title, other_doc.source_path as source_path, 
               direction, depth
        ORDER BY depth
        """ % (depth, depth)
        
        results = await self.graph_client.execute_query(query, {"document_id": document_id})
        return [dict(record) for record in results]
```

4. **Integration with Agent Responses**:
```python
async def build_response_with_references(query, response_text, conversation_id=None):
    """Build agent response with document references"""
    # Get relevant documents
    relevant_docs = await retriever.get_relevant_documents(query, conversation_id)
    
    # Format citations
    citations = []
    for i, doc in enumerate(relevant_docs):
        source_path = doc.get("source_path")
        title = doc.get("title") or os.path.basename(source_path)
        author = doc.get("author", "Unknown")
        updated_at = doc.get("updated_at", "Unknown date")
        
        citation = f"[{i+1}] {title} ({author}, {updated_at})"
        if source_path:
            citation += f"\nPath: {source_path}"
        
        citations.append(citation)
    
    # Build response
    if citations:
        response_with_refs = f"{response_text}\n\nReferences:\n" + "\n".join(citations)
        return response_with_refs
    
    return response_text
```

5. **Source Path Standardization**:
```python
def standardize_source_path(path):
    """Standardize source paths for consistent reference matching"""
    # Convert to absolute path if possible
    if os.path.exists(path):
        path = os.path.abspath(path)
    
    # Normalize path separators
    path = path.replace('\\', '/')
    
    # Remove URI schemes if present
    uri_schemes = ['file://', 'http://', 'https://']
    for scheme in uri_schemes:
        if path.startswith(scheme):
            path = path[len(scheme):]
    
    return path
```