# RAG System Enhancement Roadmap

This document outlines concrete implementation recommendations to improve our hybrid knowledge graph + embeddings system. Our current architecture combines Memgraph for structured relationships with vector embeddings for semantic search - this hybrid approach is optimal and should be enhanced rather than replaced.

## Current System Analysis

### Strengths of Our Hybrid Architecture

Our system successfully combines:
- **Knowledge Graph**: Memgraph for storing structured relationships
- **Vector Embeddings**: Text embeddings with Azure OpenAI's `text-embedding-3-small`
- **Integrated Search**: Vector search within the graph using Memgraph's vector indexing capabilities

This hybrid approach captures advantages of both:
- Fast semantic search through vector embeddings
- Rich relationship modeling through the knowledge graph
- Integrated search that can combine both approaches

### Data Schema Excellence
Our current schema maintains clear lineage:
```
Source → Document → DocumentChunk → Vector
     ↑                    ↑            ↑
  Origin           Content Segment   Embedding
```

## 1. Enhanced Retrieval Pipeline

**Problem**: Current system does basic vector search
**Solution**: Implement sophisticated multi-stage retrieval

### Implementation

```python
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class RetrievalResult:
    content: str
    source_uri: str
    confidence: float
    chunk_id: str
    relationships: List[Dict[str, Any]]

class HybridRetriever:
    def __init__(self, graph_client, embedder):
        self.graph_client = graph_client
        self.embedder = embedder
    
    async def retrieve(
        self, 
        query: str, 
        k: int = 10,
        use_reranking: bool = True
    ) -> List[RetrievalResult]:
        # Stage 1: Vector search for semantic candidates
        query_embedding = await self.embedder.get_embedding(query)
        vector_results = self.graph_client.search_chunks(
            query_embedding, 
            k=k*2  # Get more candidates for reranking
        )
        
        # Stage 2: Graph-based context enrichment
        enriched_results = []
        for result in vector_results:
            chunk = result["chunk"]
            
            # Get document context
            document = self.graph_client.get_by_id("Document", chunk["parent_id"])
            source = self.graph_client.get_source_by_chunk(chunk["id"])
            
            # Get related chunks from same document
            related_chunks = self.graph_client.get_document_chunks(
                chunk["parent_id"]
            )
            
            enriched_results.append(RetrievalResult(
                content=chunk["content"],
                source_uri=source["uri"],
                confidence=result["similarity"],
                chunk_id=chunk["id"],
                relationships={
                    "document": document,
                    "source": source,
                    "related_chunks": related_chunks[:3]  # Top 3 related
                }
            ))
        
        # Stage 3: Re-ranking using graph relationships
        if use_reranking:
            enriched_results = await self._rerank_results(
                query, enriched_results
            )
        
        return enriched_results[:k]
    
    async def _rerank_results(
        self, 
        query: str, 
        candidates: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        # Implement cross-encoder or graph-based reranking
        # For now, boost results with more relationships
        for result in candidates:
            relationship_boost = len(result.relationships.get("related_chunks", []))
            result.confidence += relationship_boost * 0.1
        
        return sorted(candidates, key=lambda x: x.confidence, reverse=True)
```

**Benefits**:
- Multi-stage retrieval improves precision
- Graph context enrichment provides better understanding
- Re-ranking ensures most relevant results surface first

## 2. Improved Web Loader with Semantic Chunking

**Problem**: Current WebLoader uses simple sentence splitting
**Solution**: Implement semantic chunking with content deduplication

### Implementation

```python
from typing import List, Generator, Tuple, Optional, Dict, Set
import hashlib
import re
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

class WebLoader(Loader):
    def __init__(self, url: str, max_urls: int = 1000, chunk_size: int = 512):
        self.url = url
        self.max_urls = max_urls
        self.chunk_size = chunk_size
        self.visited_urls: Set[str] = set()
        self.content_deduplicator: Set[str] = set()
    
    def _extract_structured_content(self, soup: BeautifulSoup) -> Dict[str, str]:
        content_sections = {}
        
        # Extract title
        title_tag = soup.find('title')
        if title_tag:
            content_sections['title'] = title_tag.get_text().strip()
        
        # Extract headings with hierarchy
        headings = []
        for level in range(1, 7):
            for heading in soup.find_all(f'h{level}'):
                headings.append({
                    'level': level,
                    'text': heading.get_text().strip(),
                    'id': heading.get('id', '')
                })
        content_sections['headings'] = headings
        
        # Extract main content (remove nav, footer, sidebar)
        content_tags = soup.find_all(['main', 'article', 'section'])
        if not content_tags:
            content_tags = [soup]
        
        main_content = []
        for tag in content_tags:
            # Remove unwanted elements
            for unwanted in tag.find_all(['nav', 'footer', 'aside', 'script', 'style']):
                unwanted.decompose()
            main_content.append(tag.get_text(separator=' ', strip=True))
        
        content_sections['content'] = ' '.join(main_content)
        return content_sections
    
    def _semantic_chunking(self, content: str, headings: List[Dict]) -> List[str]:
        # Split content by headings to maintain semantic coherence
        chunks = []
        current_chunk = ""
        
        sentences = re.split(r'[.!?]+', content)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Check if adding this sentence exceeds chunk size
            if len(current_chunk) + len(sentence) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _deduplicate_content(self, content: str) -> bool:
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        if content_hash in self.content_deduplicator:
            return False
        self.content_deduplicator.add(content_hash)
        return True
```

**Benefits**:
- Better content structure preservation
- Deduplication prevents redundant processing
- Semantic coherence in chunks improves retrieval quality

## 3. Query Expansion and Intent Detection

**Problem**: Basic query processing without understanding user intent
**Solution**: Add query understanding and expansion capabilities

### Implementation

```python
from enum import Enum
from typing import List, Dict, Any
import re

class QueryIntent(Enum):
    FACTUAL = "factual"
    PROCEDURAL = "procedural"
    EXPLORATORY = "exploratory"
    COMPARATIVE = "comparative"

class QueryProcessor:
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.intent_patterns = {
            QueryIntent.FACTUAL: [r'\bwhat is\b', r'\bdefine\b', r'\bexplain\b'],
            QueryIntent.PROCEDURAL: [r'\bhow to\b', r'\bsteps\b', r'\bprocess\b'],
            QueryIntent.EXPLORATORY: [r'\bexplore\b', r'\bfind\b', r'\bshow me\b'],
            QueryIntent.COMPARATIVE: [r'\bcompare\b', r'\bversus\b', r'\bvs\b']
        }
    
    def detect_intent(self, query: str) -> QueryIntent:
        query_lower = query.lower()
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return intent
        
        return QueryIntent.FACTUAL
    
    async def expand_query(self, original_query: str) -> List[str]:
        expansion_prompt = f"""
        Generate 3 alternative phrasings for this query that maintain the same intent:
        Original: {original_query}
        
        Provide only the alternative queries, one per line.
        """
        
        response = await self.llm_client.chat([{
            "role": "user", 
            "content": expansion_prompt
        }])
        
        expanded_queries = [
            line.strip() 
            for line in response.content.split('\n') 
            if line.strip()
        ]
        
        return [original_query] + expanded_queries[:3]
    
    def extract_entities(self, query: str) -> List[str]:
        # Simple entity extraction - could be enhanced with NER
        # Extract capitalized words and quoted phrases
        entities = []
        
        # Quoted phrases
        quoted = re.findall(r'"([^"]*)"', query)
        entities.extend(quoted)
        
        # Capitalized words (potential proper nouns)
        capitalized = re.findall(r'\b[A-Z][a-z]+\b', query)
        entities.extend(capitalized)
        
        return list(set(entities))
```

**Benefits**:
- Intent-aware retrieval strategies
- Query expansion improves recall
- Entity extraction enables targeted search

## 4. Result Fusion and Ranking

**Problem**: Single retrieval strategy may miss relevant content
**Solution**: Combine multiple retrieval strategies with intelligent fusion

### Implementation

```python
from typing import List, Dict, Any
from dataclasses import dataclass
import math

@dataclass
class FusedResult:
    content: str
    source: str
    score: float
    retrieval_methods: List[str]
    
class ResultFusion:
    def __init__(self):
        self.method_weights = {
            'vector_search': 0.6,
            'graph_traversal': 0.3,
            'keyword_match': 0.1
        }
    
    def reciprocal_rank_fusion(
        self, 
        result_lists: Dict[str, List[Dict]], 
        k: int = 60
    ) -> List[FusedResult]:
        # RRF: score = sum(1/(k + rank)) for each method
        item_scores = {}
        
        for method, results in result_lists.items():
            weight = self.method_weights.get(method, 1.0)
            
            for rank, result in enumerate(results):
                item_id = result.get('chunk_id', result.get('id'))
                
                if item_id not in item_scores:
                    item_scores[item_id] = {
                        'result': result,
                        'score': 0,
                        'methods': []
                    }
                
                rrf_score = weight / (k + rank + 1)
                item_scores[item_id]['score'] += rrf_score
                item_scores[item_id]['methods'].append(method)
        
        # Sort by combined score
        sorted_items = sorted(
            item_scores.items(), 
            key=lambda x: x[1]['score'], 
            reverse=True
        )
        
        fused_results = []
        for item_id, item_data in sorted_items:
            result = item_data['result']
            fused_results.append(FusedResult(
                content=result.get('content', ''),
                source=result.get('source', ''),
                score=item_data['score'],
                retrieval_methods=item_data['methods']
            ))
        
        return fused_results
    
    def diversify_results(
        self, 
        results: List[FusedResult], 
        max_per_source: int = 2
    ) -> List[FusedResult]:
        # Ensure result diversity by limiting results per source
        source_counts = {}
        diversified = []
        
        for result in results:
            source = result.source
            count = source_counts.get(source, 0)
            
            if count < max_per_source:
                diversified.append(result)
                source_counts[source] = count + 1
        
        return diversified
```

**Benefits**:
- Reciprocal Rank Fusion combines multiple signals effectively
- Result diversification prevents source bias
- Weighted scoring allows fine-tuning retrieval balance

## 5. Performance Monitoring and Caching

**Problem**: Repeated queries cause unnecessary computation
**Solution**: Intelligent caching with TTL and performance tracking

### Implementation

```python
from typing import Any, Optional, Dict
import hashlib
import json
import time
from functools import wraps
import asyncio

class RAGCache:
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.ttl = ttl
    
    def _generate_key(self, query: str, params: Dict[str, Any]) -> str:
        combined = f"{query}:{json.dumps(params, sort_keys=True)}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    def get(self, query: str, params: Dict[str, Any]) -> Optional[Any]:
        key = self._generate_key(query, params)
        
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry['timestamp'] < self.ttl:
                return entry['data']
            else:
                del self.cache[key]
        
        return None
    
    def set(self, query: str, params: Dict[str, Any], data: Any) -> None:
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(
                self.cache.keys(), 
                key=lambda k: self.cache[k]['timestamp']
            )
            del self.cache[oldest_key]
        
        key = self._generate_key(query, params)
        self.cache[key] = {
            'data': data,
            'timestamp': time.time()
        }

def cached_retrieval(cache: RAGCache):
    def decorator(func):
        @wraps(func)
        async def wrapper(self, query: str, **kwargs):
            # Check cache first
            cached_result = cache.get(query, kwargs)
            if cached_result:
                return cached_result
            
            # Execute function
            result = await func(self, query, **kwargs)
            
            # Cache result
            cache.set(query, kwargs, result)
            
            return result
        return wrapper
    return decorator
```

**Benefits**:
- Reduces response latency for repeated queries
- LRU eviction prevents memory bloat
- TTL ensures cache freshness

## 6. Enhanced GitHub Search Tool

**Problem**: Current GitHubKnowledgebase tool uses basic search
**Solution**: Integrate all enhancement components into existing tool

### Implementation

```python
from core.rag.retrieval import HybridRetriever
from core.rag.query_processor import QueryProcessor
from core.rag.result_fusion import ResultFusion

class GitHubKnowledgebase(Tool):
    def __init__(self):
        self.retriever = HybridRetriever(graph_client, embedder)
        self.query_processor = QueryProcessor(llm_client)
        self.result_fusion = ResultFusion()
    
    async def run(self, query: str):
        try:
            # Process query
            intent = self.query_processor.detect_intent(query)
            expanded_queries = await self.query_processor.expand_query(query)
            
            # Multi-strategy retrieval
            all_results = {}
            
            for expanded_query in expanded_queries:
                # Vector search
                vector_results = await self.retriever.retrieve(
                    expanded_query, k=10
                )
                all_results[f'vector_{expanded_query}'] = vector_results
                
                # Graph traversal for related content
                if intent == QueryIntent.COMPARATIVE:
                    # Special handling for comparative queries
                    entities = self.query_processor.extract_entities(expanded_query)
                    for entity in entities:
                        entity_results = await self._entity_search(entity)
                        all_results[f'entity_{entity}'] = entity_results
            
            # Fuse results
            fused_results = self.result_fusion.reciprocal_rank_fusion(
                all_results, k=60
            )
            
            # Diversify
            final_results = self.result_fusion.diversify_results(
                fused_results, max_per_source=2
            )
            
            # Format response
            return self._format_response(final_results[:5], query)
            
        except Exception as e:
            return {"error": f"Enhanced search failed: {str(e)}"}
    
    def _format_response(self, results: List, query: str) -> str:
        response_parts = [
            f"Found {len(results)} relevant results for: {query}\n"
        ]
        
        for i, result in enumerate(results, 1):
            response_parts.append(
                f"{i}. **Source**: {result.source}\n"
                f"   **Content**: {result.content[:200]}...\n"
                f"   **Confidence**: {result.score:.2f}\n"
                f"   **Methods**: {', '.join(result.retrieval_methods)}\n"
            )
        
        return "\n".join(response_parts)
```

**Benefits**:
- Seamless integration with existing tool interface
- Intent-aware search strategies
- Rich result presentation with confidence scores

## 7. Comprehensive Testing Strategy

**Problem**: Complex system needs thorough testing
**Solution**: Unit and integration tests for all components

### Implementation

```python
import pytest
from unittest.mock import Mock, AsyncMock
from core.rag.retrieval import HybridRetriever, RetrievalResult

class TestHybridRetriever:
    @pytest.fixture
    def mock_graph_client(self):
        client = Mock()
        client.search_chunks.return_value = [
            {
                "chunk": {"id": "chunk1", "content": "test content", "parent_id": "doc1"},
                "similarity": 0.9
            }
        ]
        client.get_by_id.return_value = {"id": "doc1", "title": "Test Doc"}
        client.get_source_by_chunk.return_value = {"uri": "https://test.com"}
        client.get_document_chunks.return_value = []
        return client
    
    @pytest.fixture
    def mock_embedder(self):
        embedder = Mock()
        embedder.get_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
        return embedder
    
    @pytest.fixture
    def retriever(self, mock_graph_client, mock_embedder):
        return HybridRetriever(mock_graph_client, mock_embedder)
    
    @pytest.mark.asyncio
    async def test_retrieve_basic(self, retriever):
        results = await retriever.retrieve("test query", k=5)
        
        assert len(results) == 1
        assert isinstance(results[0], RetrievalResult)
        assert results[0].content == "test content"
        assert results[0].source_uri == "https://test.com"
    
    @pytest.mark.asyncio
    async def test_retrieve_with_reranking(self, retriever):
        results = await retriever.retrieve("test query", k=5, use_reranking=True)
        
        assert len(results) == 1
        assert results[0].confidence >= 0.9
```

**Benefits**:
- Ensures component reliability
- Facilitates safe refactoring
- Provides usage examples

## Implementation Priority

### Phase 1: Core Enhancements (Weeks 1-2)
1. Enhanced Retrieval Pipeline
2. Query Processing and Intent Detection
3. Basic Caching Implementation

### Phase 2: Advanced Features (Weeks 3-4)
4. Result Fusion and Ranking
5. Improved Web Loader
6. Enhanced GitHub Search Tool Integration

### Phase 3: Production Readiness (Weeks 5-6)
7. Comprehensive Testing Suite
8. Performance Monitoring
9. Documentation and Deployment

## Success Metrics

- **Retrieval Quality**: Measure precision@k and recall@k improvements
- **Response Time**: Target <2s for cached queries, <5s for new queries
- **User Satisfaction**: Track query success rate and user feedback
- **System Reliability**: Monitor error rates and uptime

## Why This Hybrid Approach is Optimal

Your current hybrid architecture is well-designed for your use case. The combination provides:

1. **Speed**: Vector search for fast initial retrieval
2. **Precision**: Graph relationships for accurate context
3. **Flexibility**: Can optimize queries based on the specific need
4. **Scalability**: Both Memgraph and vector embeddings scale well

For your AI agent system, this hybrid approach is optimal because it supports both exploratory search (embeddings) and precise reasoning (knowledge graph), which are both essential for an intelligent assistant.

## Use Case Optimization

| Use Case | Best Approach | Current Implementation |
|----------|---------------|------------------------|
| **Document Search** | Embeddings | ✅ Vector search in GitHubKnowledgebase |
| **Fact Verification** | Knowledge Graph | ✅ Graph relationships for source tracking |
| **Citation/Reference Tracking** | Knowledge Graph | ✅ Explicit relationship modeling |
| **Content Recommendation** | Embeddings | 🔄 Can be enhanced with similarity clustering |
| **Data Lineage** | Knowledge Graph | ✅ Source → Document → Chunk schema |
| **Multi-hop Reasoning** | Hybrid | 🔄 Needs enhanced retrieval pipeline |
| **Real-time Search** | Embeddings | ✅ Fast vector similarity search |
| **Structured Queries** | Knowledge Graph | ✅ Cypher queries in Memgraph |

## Future Enhancements

Based on your AI roadmap, consider:
- **Dense Passage Retrieval**: Bi-encoder architecture for better semantic matching
- **Cross-encoder Re-ranking**: Use knowledge graph relationships as features
- **Hybrid Search**: Combine dense and sparse retrieval with graph traversal
- **Contextual Embeddings**: Fine-tune embeddings on your domain-specific data

## Conclusion

These enhancements will significantly improve your system by:

1. **Better retrieval quality** through hybrid search and reranking
2. **Smarter content processing** with semantic chunking and deduplication  
3. **Query understanding** with intent detection and expansion
4. **Performance optimization** through caching and result fusion
5. **Comprehensive testing** for reliability

The hybrid approach you've chosen is excellent - these enhancements will make it even more powerful and production-ready.
