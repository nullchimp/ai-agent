from typing import Dict, List, Optional, Union, Any, TypedDict
import asyncio
from datetime import datetime
import os

from core.rag.graph_client import MemGraphClient
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
        graph_client: MemGraphClient,
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
        """Search for documents by topic"""
        topic_id = await self._graph_client.create_or_get_topic(topic)
        
        # Find documents belonging to this topic
        query = """
        MATCH (d:Document)-[:BELONGS_TO]->(t:Topic {id: $topic_id})
        RETURN d.path AS path, d.content AS content, d.title as title, 
               d.author as author, d.updated_at as updated_at, d.source_path as source_path
        LIMIT $limit
        """
        results = await self._graph_client.run_query(query, {"topic_id": topic_id, "limit": limit})
        
        return [{
            "path": result["path"],
            "content": result["content"],
            "title": result.get("title", os.path.basename(result["path"])),
            "source_path": result.get("source_path", ""),
            "author": result.get("author", "Unknown"),
            "updated_at": result.get("updated_at", ""),
            "score": 1.0  # All direct topic matches have score 1.0
        } for result in results]
    
    async def search_by_concept(
        self,
        concept_name: str,
        limit: int = 10
    ) -> List[RetrievalResult]:
        """Search for documents explaining a concept"""
        concept_id = await self._graph_client.create_or_get_concept(concept_name)
        
        # Find documents explaining this concept
        query = """
        MATCH (d:Document)-[:EXPLAINS]->(c:Concept {id: $concept_id})
        RETURN d.path AS path, d.content AS content, d.title as title, 
               d.author as author, d.updated_at as updated_at, d.source_path as source_path
        LIMIT $limit
        """
        results = await self._graph_client.run_query(query, {"concept_id": concept_id, "limit": limit})
        
        return [{
            "path": result["path"],
            "content": result["content"],
            "title": result.get("title", os.path.basename(result["path"])),
            "source_path": result.get("source_path", ""),
            "author": result.get("author", "Unknown"),
            "updated_at": result.get("updated_at", ""),
            "score": 1.0  # All direct concept matches have score 1.0
        } for result in results]
    
    async def find_related_concepts(
        self,
        concept_name: str,
        limit: int = 5
    ) -> List[str]:
        """Find concepts related to a given concept"""
        concept_id = await self._graph_client.create_or_get_concept(concept_name)
        
        # Find related concepts
        query = """
        MATCH (c1:Concept {id: $concept_id})-[:RELATED_TO]-(c2:Concept)
        RETURN DISTINCT c2.name as name
        LIMIT $limit
        """
        results = await self._graph_client.run_query(query, {"concept_id": concept_id, "limit": limit})
        
        return [result["name"] for result in results]
    
    async def get_document_references(
        self,
        document_path: str,
        limit: int = 10
    ) -> List[Dict]:
        """Get documents referenced by a specific document"""
        doc = await self._graph_client.find_document(document_path)
        if not doc or "id" not in doc:
            return []
            
        query = """
        MATCH (d1:Document {id: $doc_id})-[:REFERENCES]->(d2:Document)
        RETURN d2.path AS path, d2.title as title, 
               d2.author as author, d2.updated_at as updated_at, d2.source_path as source_path
        LIMIT $limit
        """
        results = await self._graph_client.run_query(query, {"doc_id": doc["id"], "limit": limit})
        
        return [{
            "path": result["path"],
            "title": result.get("title", os.path.basename(result["path"])),
            "source_path": result.get("source_path", ""),
            "author": result.get("author", "Unknown"),
            "updated_at": result.get("updated_at", "")
        } for result in results]
    
    async def get_document_citations(
        self,
        document_path: str,
        limit: int = 10
    ) -> List[Dict]:
        """Get documents that cite a specific document"""
        doc = await self._graph_client.find_document(document_path)
        if not doc or "id" not in doc:
            return []
            
        query = """
        MATCH (d1:Document)-[:REFERENCES]->(d2:Document {id: $doc_id})
        RETURN d1.path AS path, d1.title as title, 
               d1.author as author, d1.updated_at as updated_at, d1.source_path as source_path
        LIMIT $limit
        """
        results = await self._graph_client.run_query(query, {"doc_id": doc["id"], "limit": limit})
        
        return [{
            "path": result["path"],
            "title": result.get("title", os.path.basename(result["path"])),
            "source_path": result.get("source_path", ""),
            "author": result.get("author", "Unknown"),
            "updated_at": result.get("updated_at", "")
        } for result in results]
    
    async def enhanced_conversation_context(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        message_id: Optional[str] = None
    ) -> ConversationContext:
        """Enhanced get_conversation_context that also includes concept and topic relationships"""
        # Start with the base conversation context
        context = await self.get_conversation_context(query, conversation_id, message_id)
        
        # Extract concepts from the query
        # In a real implementation, this would use NLP or send to OpenAI
        # For now, we'll just use simple heuristics
        words = [w for w in query.lower().split() if len(w) > 3]
        
        # For each significant word, check if it matches any concepts
        all_concepts = []
        for word in words:
            # This query checks if there are any concepts with this name
            concept_query = """
            MATCH (c:Concept)
            WHERE toLower(c.name) CONTAINS $word
            RETURN c.name as name
            LIMIT 3
            """
            concepts = await self._graph_client.run_query(concept_query, {"word": word})
            all_concepts.extend([c["name"] for c in concepts])
        
        # Find documents that explain these concepts
        documents_from_concepts = []
        for concept in all_concepts:
            docs = await self.search_by_concept(concept, limit=2)
            documents_from_concepts.extend(docs)
        
        # Add these documents to the context if they're not already included
        existing_paths = {doc["path"] for doc in context["relevant_documents"]}
        for doc in documents_from_concepts:
            if doc["path"] not in existing_paths:
                context["relevant_documents"].append(doc)
                if "id" in doc:
                    context["document_ids"].append(doc["id"])
        
        return context

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