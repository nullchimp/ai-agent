from typing import Dict, List, Optional, Union, Any, TypedDict
import asyncio
import hashlib
from datetime import datetime

from core.rag.graph_client import MemGraphClient
from core.rag.embedding_service import EmbeddingService
from core.rag.document_loader import DocumentLoader
from core.rag.text_splitter import TextSplitter

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

class ChunkMetadata(DocumentMetadata):
    chunk_index: int
    chunk_count: int
    parent_document_id: str
    parent_document_path: str
    is_chunk: bool

class DocumentChunk(Document):
    metadata: ChunkMetadata

class Indexer:
    def __init__(
        self,
        graph_client: MemGraphClient,
        embedding_service: EmbeddingService,
        batch_size: int = 5,
        chunk_size: int = 1024,
        chunk_overlap: int = 200
    ):
        self._graph_client = graph_client
        self._embedding_service = embedding_service
        self._batch_size = batch_size
        self._document_loader = DocumentLoader()
        self._text_splitter = TextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
    
    async def load_and_index_document(self, path: str) -> List[Dict[str, Any]]:
        """Load a document from a file path and index it with chunking"""
        # Load the document
        document = self._document_loader.load_document(path)
        
        # Index the document and its chunks
        return await self.index_document_with_chunks(
            path=document["path"],
            content=document["content"],
            metadata=document.get("metadata")
        )
    
    async def load_and_index_documents(self, paths: List[str]) -> List[Dict[str, Any]]:
        """Load documents from file paths and index them with chunking"""
        # Load the documents
        documents = self._document_loader.load_documents(paths)
        
        # Index the documents and their chunks
        results = []
        for doc in documents:
            doc_results = await self.index_document_with_chunks(
                path=doc["path"],
                content=doc["content"],
                metadata=doc.get("metadata")
            )
            results.extend(doc_results)
            
        return results
    
    async def index_document_with_chunks(
        self,
        path: str,
        content: str,
        metadata: Optional[DocumentMetadata] = None
    ) -> List[Dict[str, Any]]:
        """Index a document by first creating a parent document, then chunking and indexing chunks"""
        try:
            # Generate content hash
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            
            # Check if document already exists and has the same hash
            existing_doc = await self._graph_client.find_document(path)
            if existing_doc and existing_doc.get("content_hash") == content_hash:
                return [existing_doc]  # Return existing document if unchanged
            
            # Create the parent document first
            parent_doc = await self.index_document(
                path=path,
                content=content,
                metadata=metadata,
                is_chunk=False
            )
            
            # Split the document into chunks
            document = {
                "id": parent_doc.get("id"),
                "path": path,
                "content": content,
                "metadata": metadata or {}
            }
            
            chunk_documents = self._text_splitter.split_document(document)
            
            # Index each chunk
            chunk_results = []
            for chunk_doc in chunk_documents:
                chunk_result = await self.index_document(
                    path=chunk_doc["path"],
                    content=chunk_doc["content"],
                    metadata=chunk_doc["metadata"],
                    is_chunk=True,
                    parent_id=parent_doc.get("id")
                )
                chunk_results.append(chunk_result)
            
            # Return parent and all chunks
            return [parent_doc] + chunk_results
            
        except Exception as e:
            raise ValueError(f"Failed to index document {path} with chunks: {str(e)}")
    
    async def index_document(
        self,
        path: str,
        content: str,
        metadata: Optional[DocumentMetadata] = None,
        is_chunk: bool = False,
        parent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            # Generate content hash
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            
            # Generate embedding for the document content
            embedding = await self._embedding_service.get_embedding(content)
            
            # Prepare metadata
            metadata = metadata or {}
            
            # Store the document or chunk
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
            
            # If this is a chunk, create a relationship to the parent document
            if is_chunk and parent_id:
                await self._graph_client.create_relationship(
                    from_id=result.get("id"),
                    to_id=parent_id,
                    relationship_type="CHUNK_OF"
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
                
                task = self.index_document_with_chunks(
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
                    results.extend(result)
        
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