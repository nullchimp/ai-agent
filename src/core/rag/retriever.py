from typing import Dict, List, Optional, Union, Any, TypedDict
import asyncio
from datetime import datetime

from core.rag.graph_client import Neo4jClient
from core.rag.embedding_service import EmbeddingService

class RetrievalResult(TypedDict):
    content: str
    path: str
    score: float
    title: Optional[str]
    source_path: Optional[str]
    author: Optional[str]
    updated_at: Optional[str]
    document_id: Optional[str]

class ConversationContext(TypedDict):
    relevant_documents: List[RetrievalResult]
    relevant_messages: List[Dict[str, Any]]
    document_ids: List[str]

class Retriever:
    def __init__(
        self,
        graph_client: Neo4jClient,
        embedding_service: EmbeddingService
    ):
        self._graph_client = graph_client
        self._embedding_service = embedding_service
    
    async def search_documents(
        self,
        query: str,
        limit: int = 5,
        min_score: float = 0.5
    ) -> List[RetrievalResult]:
        try:
            # Generate embedding for the query
            query_embedding = await self._embedding_service.get_embedding(query)
            
            # Search for relevant documents
            search_results = await self._graph_client.semantic_search(query_embedding, limit)
            
            # Filter by minimum score if specified
            if min_score > 0:
                search_results = [r for r in search_results if r.get('score', 0) >= min_score]
            
            # Format results
            results = []
            for result in search_results:
                retrieval_result: RetrievalResult = {
                    'content': result.get('content', ''),
                    'path': result.get('path', ''),
                    'score': result.get('score', 0.0),
                    'title': result.get('title'),
                    'source_path': result.get('source_path'),
                    'author': result.get('author'),
                    'updated_at': result.get('updated_at'),
                    'document_id': result.get('id')
                }
                results.append(retrieval_result)
            
            return results
        except Exception as e:
            # If vector search fails, try fallback
            try:
                fallback_results = await self._graph_client.semantic_search_fallback(
                    query_embedding, limit
                )
                results = []
                for result in fallback_results:
                    retrieval_result: RetrievalResult = {
                        'content': result.get('content', ''),
                        'path': result.get('path', ''),
                        'score': result.get('score', 0.0),
                        'title': result.get('title'),
                        'source_path': result.get('source_path'),
                        'author': result.get('author'),
                        'updated_at': result.get('updated_at'),
                        'document_id': result.get('id')
                    }
                    results.append(retrieval_result)
                return results
            except Exception as fallback_error:
                print(f"Both vector search and fallback failed: {str(fallback_error)}")
                return []
    
    async def get_conversation_context(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        message_id: Optional[str] = None
    ) -> ConversationContext:
        # Generate embedding for the query
        query_embedding = await self._embedding_service.get_embedding(query)
        
        # Use conversation-aware search if conversation ID is provided
        if conversation_id:
            search_results = await self._graph_client.conversation_aware_search(
                query_embedding, 
                conversation_id=conversation_id, 
                limit=5
            )
        else:
            search_results = await self._graph_client.semantic_search(query_embedding, limit=5)
        
        # Format document results
        documents = []
        document_ids = []
        relevant_messages = []
        
        for result in search_results:
            # Check if this is from conversation history
            if result.get('path', '').startswith('conversation/'):
                # Extract conversation messages
                relevant_messages.append({
                    'content': result.get('content', ''),
                    'conversation_id': result.get('path').split('/')[-1],
                    'relevance': result.get('score', 0.0),
                    'title': result.get('title', ''),
                })
            else:
                # It's a document
                retrieval_result: RetrievalResult = {
                    'content': result.get('content', ''),
                    'path': result.get('path', ''),
                    'score': result.get('score', 0.0),
                    'title': result.get('title'),
                    'source_path': result.get('source_path'),
                    'author': result.get('author'),
                    'updated_at': result.get('updated_at'),
                    'document_id': result.get('id')
                }
                documents.append(retrieval_result)
                
                if result.get('id'):
                    document_ids.append(result.get('id'))
        
        # If we have message_id, link it to the relevant documents
        if message_id and document_ids:
            for doc_id in document_ids:
                try:
                    await self._graph_client.create_message_document_reference(message_id, doc_id)
                except Exception as e:
                    print(f"Error linking message to document: {str(e)}")
        
        return {
            'relevant_documents': documents,
            'relevant_messages': relevant_messages,
            'document_ids': document_ids
        }
    
    async def hybrid_search(
        self,
        query: str,
        limit: int = 5
    ) -> List[RetrievalResult]:
        semantic_results = await self.search_documents(query, limit)
        
        # TODO: Add keyword search component here if desired
        # keyword_results = await self._keyword_search(query, limit)
        # combined_results = self._merge_search_results(semantic_results, keyword_results)
        # return combined_results
        
        return semantic_results
    
    async def search_by_topic(
        self,
        topic: str,
        limit: int = 10
    ) -> List[RetrievalResult]:
        query = f"""
        MATCH (d:Document)-[:BELONGS_TO]->(t:Topic)
        WHERE t.name =~ $topic_pattern
        RETURN d.path AS path, d.content AS content, 
               d.title AS title, d.source_path AS source_path,
               d.author AS author, d.updated_at AS updated_at
        LIMIT $limit
        """
        
        topic_pattern = f"(?i).*{topic}.*"  # Case-insensitive partial match
        results = await self._graph_client.run_query(query, {
            "topic_pattern": topic_pattern,
            "limit": limit
        })
        
        return [
            {
                'content': result.get('content', ''),
                'path': result.get('path', ''),
                'score': 1.0,  # No score for topic-based search
                'title': result.get('title'),
                'source_path': result.get('source_path'),
                'author': result.get('author'),
                'updated_at': result.get('updated_at'),
                'document_id': None
            }
            for result in results
        ]
    
    def format_retrieved_context(
        self,
        results: List[RetrievalResult],
        max_tokens: int = 1500
    ) -> str:
        context_chunks = []
        current_tokens = 0
        
        for i, result in enumerate(results):
            # Estimate tokens (rough approximation: 4 chars ≈ 1 token)
            content = result.get('content', '')
            title = result.get('title', result.get('path', 'Untitled'))
            source = result.get('source_path', 'Unknown source')
            
            # Format this chunk with metadata
            chunk = f"[Document {i+1}] {title}\nSource: {source}\n\n{content}"
            
            # Estimate token count
            token_estimate = len(chunk) // 4
            
            # If adding this chunk would exceed token limit, stop
            if current_tokens + token_estimate > max_tokens:
                break
                
            context_chunks.append(chunk)
            current_tokens += token_estimate
        
        # Combine all chunks into a single context string
        if context_chunks:
            return "\n\n" + "\n\n---\n\n".join(context_chunks)
        else:
            return ""