from typing import List, Dict, Any, Optional, Union
import re
import uuid


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
        
    def split_text(self, text: str) -> List[str]:
        """Split text into chunks with overlap"""
        if not text:
            return []
            
        # Split by separator
        splits = text.split(self.separator)
        
        # Join splits together to form chunks
        chunks = []
        current_chunk = []
        current_chunk_size = 0
        
        for split in splits:
            # Calculate size of potential chunk including separator
            split_size = len(split) + len(self.separator)
            
            if current_chunk_size + split_size > self.chunk_size and current_chunk:
                # If adding this split would exceed chunk size, create a new chunk
                chunks.append(self.separator.join(current_chunk))
                
                # Start new chunk with overlap
                # Take elements from the end of the current chunk that fit within overlap size
                overlap_size = 0
                overlap_elements = []
                
                # Go backward through current_chunk to find elements that fit in overlap
                # but make sure we have at least one element for overlap if possible
                for element in reversed(current_chunk):
                    element_size = len(element) + len(self.separator)
                    if overlap_size + element_size <= self.chunk_overlap or not overlap_elements:
                        overlap_elements.append(element)
                        overlap_size += element_size
                    else:
                        break
                
                # Reverse the overlap elements to maintain original order
                current_chunk = list(reversed(overlap_elements))
                current_chunk_size = sum(len(e) + len(self.separator) for e in current_chunk)
            
            # Add the current split
            current_chunk.append(split)
            current_chunk_size += split_size
        
        # Add the final chunk if it's not empty
        if current_chunk:
            chunks.append(self.separator.join(current_chunk))
            
        return chunks
        
    def split_document(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split a document into multiple chunks with overlap"""
        if not document or "content" not in document or not document["content"]:
            return []
            
        # Get document content and metadata
        content = document["content"]
        path = document.get("path", "")
        metadata = document.get("metadata", {})
        
        # Split the content into chunks
        text_chunks = self.split_text(content)
        
        # Create a document for each chunk with appropriate metadata
        chunk_documents = []
        parent_doc_id = document.get("id", str(uuid.uuid4()))
        
        for i, chunk_text in enumerate(text_chunks):
            chunk_id = f"{parent_doc_id}_chunk_{i}"
            chunk_path = f"{path}#chunk{i}"
            
            # Create chunk document with reference to parent
            chunk_document = {
                "id": chunk_id,
                "path": chunk_path,
                "content": chunk_text,
                "metadata": {
                    **metadata,
                    "chunk_index": i,
                    "chunk_count": len(text_chunks),
                    "parent_document_id": parent_doc_id,
                    "parent_document_path": path,
                    "is_chunk": True
                }
            }
            
            chunk_documents.append(chunk_document)
            
        return chunk_documents