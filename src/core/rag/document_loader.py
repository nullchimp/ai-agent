from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import os

from llama_index.core.readers import SimpleDirectoryReader


class DocumentLoader:
    def __init__(self):
        pass
        
    def load_document(self, path: str) -> Dict[str, Any]:
        """Load a document from a file path"""
        abs_path = os.path.abspath(path)
        file_extension = Path(path).suffix.lower()
        
        # Use SimpleDirectoryReader to load the file
        try:
            # Check if path exists
            if not os.path.exists(abs_path):
                raise ValueError(f"File not found: {abs_path}")
                
            # Get directory and filename
            directory = os.path.dirname(abs_path)
            filename = os.path.basename(abs_path)
            
            # Load the document using SimpleDirectoryReader
            reader = SimpleDirectoryReader(
                input_dir=directory,
                filename_as_id=True,
                file_extractor={
                    # Will handle most document types automatically
                },
                required_exts=[file_extension[1:]]  # Remove the dot from extension
            )
            
            # Only load the specific file
            docs = list(filter(
                lambda doc: os.path.basename(doc.metadata.get("file_path", "")) == filename,
                reader.load_data()
            ))
            
            if not docs:
                raise ValueError(f"Failed to load document: {path}")
                
            # Extract content and metadata
            doc = docs[0]
            content = doc.text
            metadata = doc.metadata
                
            # Format as a document dict
            document = {
                "path": path,
                "content": content,
                "metadata": {
                    "title": metadata.get("title", os.path.basename(path)),
                    "mime_type": self._get_mime_type(file_extension),
                    "source_type": "file",
                    "source_uri": f"file://{abs_path}",
                    **metadata
                }
            }
            
            return document
            
        except Exception as e:
            raise ValueError(f"Failed to load document {path}: {str(e)}")
    
    def load_documents(self, paths: List[str]) -> List[Dict[str, Any]]:
        """Load multiple documents from file paths"""
        documents = []
        for path in paths:
            try:
                document = self.load_document(path)
                documents.append(document)
            except Exception as e:
                print(f"Error loading document {path}: {str(e)}")
        
        return documents
    
    def _get_mime_type(self, extension: str) -> str:
        """Map file extensions to MIME types"""
        mime_map = {
            ".pdf": "application/pdf",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".html": "text/html",
            ".htm": "text/html",
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".py": "text/x-python",
            ".js": "application/javascript",
            ".json": "application/json",
            ".java": "text/x-java",
            ".c": "text/x-c",
            ".cpp": "text/x-c++",
        }
        
        return mime_map.get(extension.lower(), "text/plain")