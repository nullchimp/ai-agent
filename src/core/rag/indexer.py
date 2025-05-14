from typing import Dict, List, Optional, Union, Any, TypedDict
import asyncio
import hashlib
from datetime import datetime

from core.rag.graph_client import MemGraphClient
from core.rag.embedding_service import EmbeddingService

class DocumentMetadata(TypedDict, total=False):
    title: Optional[str]
    author: Optional[str] 
    source_type: str
    source_uri: str
    mime_type: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]

class Document(TypedDict):
    id: Optional[str]
    path: str
    content: str
    metadata: DocumentMetadata

class Indexer:
    def __init__(
        self,
        graph_client: MemGraphClient,
        embedding_service: EmbeddingService,
        batch_size: int = 5
    ):
        self._graph_client = graph_client
        self._embedding_service = embedding_service
        self._batch_size = batch_size
    
    async def index_document(
        self,
        path: str,
        content: str,
        metadata: Optional[DocumentMetadata] = None
    ) -> Dict[str, Any]:
        try:
            # Generate content hash
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            
            # Check if document already exists and has the same hash
            existing_doc = await self._graph_client.find_document(path)
            if existing_doc and existing_doc.get("content_hash") == content_hash:
                return existing_doc
            
            # Generate embedding for the document content
            embedding = await self._embedding_service.get_embedding(content)
            
            # Prepare metadata
            metadata = metadata or {}
            
            # Store the document
            result = await self._graph_client.upsert_document(
                path=path,
                content=content,
                embedding=embedding,
                content_hash=content_hash,
                embedding_version="text-embedding-ada-002",
                updated_at=metadata.get("updated_at", datetime.now().isoformat()),
                title=metadata.get("title"),
                author=metadata.get("author"),
                mime_type=metadata.get("mime_type")
            )
            
            return result
        except Exception as e:
            raise ValueError(f"Failed to index document {path}: {str(e)}")
    
    async def index_documents(
        self,
        documents: List[Union[Document, Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        results = []
        
        # Process in batches to avoid overwhelming the embedding API
        for i in range(0, len(documents), self._batch_size):
            batch = documents[i:i+self._batch_size]
            batch_tasks = []
            
            for doc in batch:
                # Handle both Document type and dict format
                path = doc["path"]
                content = doc["content"]
                metadata = doc.get("metadata", {})
                
                task = self.index_document(
                    path=path,
                    content=content,
                    metadata=metadata
                )
                batch_tasks.append(task)
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            for result in batch_results:
                if isinstance(result, Exception):
                    # Log error but continue processing
                    print(f"Error during batch indexing: {str(result)}")
                else:
                    results.append(result)
        
        return results
    
    async def extract_and_index_symbols(self, document_path: str, symbols: List[str]) -> List[Dict[str, Any]]:
        results = []
        for symbol in symbols:
            try:
                result = await self._graph_client.create_symbol(symbol, document_path)
                results.append(result)
            except Exception as e:
                print(f"Error creating symbol {symbol}: {str(e)}")
        return results
    
    async def extract_and_index_resources(self, document_path: str, resources: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Index various resource types that a document references
        
        Args:
            document_path: Path to the document that references the resources
            resources: List of resource dictionaries with uri, type, and optional description
        """
        results = []
        for resource in resources:
            try:
                uri = resource.get("uri")
                resource_type = resource.get("type", "unknown")
                description = resource.get("description")
                
                if uri:
                    # Create the resource and create a REFERENCES relationship
                    doc = await self._graph_client.find_document(document_path)
                    if doc and "id" in doc:
                        result = await self._graph_client.link_document_to_resource(
                            doc["id"], uri, resource_type
                        )
                        results.append(result)
            except Exception as e:
                print(f"Error creating resource link {resource.get('uri')}: {str(e)}")
        return results
    
    async def extract_and_index_urls(self, document_path: str, urls: List[str]) -> List[Dict[str, Any]]:
        """Legacy method - now uses resources with web type"""
        resources = [{"uri": url, "type": "web", "description": "Web resource"} for url in urls]
        return await self.extract_and_index_resources(document_path, resources)
    
    async def index_document_relations(
        self,
        from_document_path: str,
        to_document_paths: List[str],
        relationship_type: str = "REFERENCES"
    ) -> List[Dict[str, Any]]:
        results = []
        for to_path in to_document_paths:
            try:
                # Convert paths to document IDs
                from_doc = await self._graph_client.find_document(from_document_path)
                to_doc = await self._graph_client.find_document(to_path)
                
                if from_doc and to_doc:
                    result = await self._graph_client.create_relationship(
                        from_id=from_doc["id"],
                        to_id=to_doc["id"],
                        relationship_type=relationship_type
                    )
                    results.append(result)
            except Exception as e:
                print(f"Error creating document relation: {str(e)}")
        return results