from typing import List, Generator, Tuple
import os
import uuid
import hashlib

from llama_index.core.readers import SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter

from .schema import Document, DocumentChunk

class DocumentLoader:
    def __init__(self, chunk_size: int = 1024, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.sentence_splitter = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
    def load_document_chunks(self, path: str) -> Generator[Tuple[Document, List[DocumentChunk]], None, None]:
        path = os.path.abspath(path)

        try:
            # Check if path exists
            if not os.path.exists(path):
                raise ValueError(f"File not found: {path}")

            # Load the document using SimpleDirectoryReader
            reader = SimpleDirectoryReader(
                input_dir=path,
                filename_as_id=True,
                recursive=True
            )

            docs = reader.load_data()
            if not docs:
                raise ValueError(f"Failed to load document: {path}")
            
            for doc in docs:
                # Check if the document is empty
                if not doc.text:
                    continue
                
                # Create parent document
                content_hash = hashlib.md5(doc.text.encode()).hexdigest()
                parent_doc = Document(
                    id=str(uuid.uuid4()),
                    path=path,
                    content=doc.text,
                    title=os.path.basename(doc.metadata.get("file_path", "Untitled")),
                    source_uri=doc.metadata.get("file_path", ""),
                    content_hash=content_hash
                )
                
                # Split document into sentence chunks with overlap
                nodes = self.sentence_splitter.get_nodes_from_documents([doc])
                
                chunks = []
                for idx, node in enumerate(nodes):
                    chunk_content = node.text
                    chunk_hash = hashlib.sha256(chunk_content.encode()).hexdigest()

                    doc_chunk = DocumentChunk(
                        id=str(uuid.uuid4()),
                        path=path,
                        content=chunk_content,
                        parent_document_id=parent_doc.id,
                        chunk_index=idx,
                        token_count=len(chunk_content.split()),
                        content_hash=chunk_hash
                    )
                    
                    chunks.append(doc_chunk)
                
                yield parent_doc, chunks

        except Exception as e:
            raise ValueError(f"Failed to load document {path}: {str(e)}")