from typing import Dict, List, Optional, Union, Any
import os
import asyncio
import hashlib
from datetime import datetime
import mimetypes
import uuid

from core.rag.graph_client import MemGraphClient
from core.rag.embedding_service import EmbeddingService

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
        title: Optional[str] = None,
        author: Optional[str] = None,
        mime_type: Optional[str] = None
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
            
            # Determine mimetype if not provided
            if not mime_type and os.path.exists(path):
                mime_type, _ = mimetypes.guess_type(path)
            
            # Store the document
            result = await self._graph_client.upsert_document(
                path=path,
                content=content,
                embedding=embedding,
                content_hash=content_hash,
                embedding_version="text-embedding-ada-002",
                updated_at=datetime.now().isoformat(),
                title=title,
                author=author,
                mime_type=mime_type
            )
            
            return result
        except Exception as e:
            raise ValueError(f"Failed to index document {path}: {str(e)}")
    
    async def index_documents(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        results = []
        
        # Process in batches to avoid overwhelming the embedding API
        for i in range(0, len(documents), self._batch_size):
            batch = documents[i:i+self._batch_size]
            batch_tasks = []
            
            for doc in batch:
                task = self.index_document(
                    path=doc["path"],
                    content=doc["content"],
                    title=doc.get("title"),
                    author=doc.get("author"),
                    mime_type=doc.get("mime_type")
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
    
    async def index_file(
        self,
        file_path: str,
        title: Optional[str] = None,
        author: Optional[str] = None,
        mime_type: Optional[str] = None
    ) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
        except UnicodeDecodeError:
            # Try binary read for non-text files
            with open(file_path, 'rb') as file:
                content = f"Binary file: {file_path}"
        
        # Index the document
        return await self.index_document(
            path=file_path,
            content=content,
            title=title or os.path.basename(file_path),
            author=author,
            mime_type=mime_type
        )
    
    async def index_directory(
        self,
        directory_path: str,
        file_extensions: Optional[List[str]] = None,
        recursive: bool = True,
        exclude_dirs: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        if not os.path.isdir(directory_path):
            raise NotADirectoryError(f"Directory not found: {directory_path}")
        
        indexed_files = []
        exclude_dirs = exclude_dirs or ['.git', '.venv', '__pycache__', 'node_modules']
        
        # Helper to check if file should be indexed based on extension
        def should_index_file(filename: str) -> bool:
            if not file_extensions:
                return True
            return any(filename.endswith(ext) for ext in file_extensions)
        
        # Walk directory and index files
        for root, dirs, files in os.walk(directory_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            if not recursive:
                # Clear dirs to prevent recursion
                dirs.clear()
            
            for file in files:
                if should_index_file(file):
                    file_path = os.path.join(root, file)
                    try:
                        result = await self.index_file(file_path)
                        indexed_files.append(result)
                    except Exception as e:
                        print(f"Error indexing file {file_path}: {str(e)}")
        
        return indexed_files
    
    async def extract_and_index_symbols(self, document_path: str, symbols: List[str]) -> List[Dict[str, Any]]:
        results = []
        for symbol in symbols:
            try:
                result = await self._graph_client.create_symbol(symbol, document_path)
                results.append(result)
            except Exception as e:
                print(f"Error creating symbol {symbol}: {str(e)}")
        return results
    
    async def extract_and_index_urls(self, document_path: str, urls: List[str]) -> List[Dict[str, Any]]:
        results = []
        for url in urls:
            try:
                result = await self._graph_client.create_url_link(url, document_path)
                results.append(result)
            except Exception as e:
                print(f"Error creating URL link {url}: {str(e)}")
        return results
    
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