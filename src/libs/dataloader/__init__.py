import os
from typing import List, Generator, Tuple, Any

from llama_index.core.node_parser import SentenceSplitter
from core.rag.schema import Document, DocumentChunk, Source

class Loader:
    def __init__(self, path, file_types: List[str] = None, recursive = True, chunk_size: int = 1024, chunk_overlap: int = 200):
        if not os.path.exists(path):
            raise ValueError(f"File not found: {path}")
        
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.sentence_splitter = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        self.recursive = recursive
        self.path = path
        self.file_types = file_types

    def create_source(self) -> Source:
        raise NotImplementedError("Subclasses should implement this method.")

    def load_data(self) -> Generator[Tuple[Document, List[DocumentChunk]], None, Source]:
        raise NotImplementedError("Subclasses should implement this method.")