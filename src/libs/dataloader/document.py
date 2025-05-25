from typing import List, Generator, Tuple
import os
import uuid
import hashlib

from . import Loader

from llama_index.core.readers import SimpleDirectoryReader

from core.rag.schema import Document, DocumentChunk, Source

class DocumentLoader(Loader):
    def create_source(self, source_path) -> Document:
        if not self.path:
            raise ValueError("Path cannot be empty.")

        source = Source(
            name=source_path.split("/")[-1],
            type="file",
            uri=source_path
        )

        source.id = hashlib.sha256(self.path.encode()).hexdigest()[:16]
        source.add_metadata(**{
            "file_type": source_path.split(".")[-1],
            "directory": "/".join(source_path.split("/")[:-1])
        })
        
        return source

    def load_data(self) -> Generator[Tuple[Document, List[DocumentChunk]], Source]:
        try:
            path = os.path.abspath(self.path)

            # Load the document using SimpleDirectoryReader
            reader = SimpleDirectoryReader(
                input_dir=path,
                filename_as_id=True,
                recursive=self.recursive
            )

            docs = reader.load_data()
            if not docs:
                raise ValueError(f"Failed to load document: {path}")
            
            for doc in docs:
                # Check if the document is empty
                if not doc.text:
                    continue
                
                source = self.create_source(doc.metadata.get("file_path", ""))

                document = Document(
                    path=path,
                    content=doc.text,
                    title=os.path.basename(doc.metadata.get("file_path", "Untitled")),
                    source_id=source.id
                )
                
                nodes = self.sentence_splitter.get_nodes_from_documents([doc])
                
                chunks = []
                for idx, node in enumerate(nodes):
                    chunk_content = node.text
                    
                    doc_chunk = DocumentChunk(
                        path=path,
                        content=chunk_content,
                        parent_id=document.id,
                        chunk_index=idx,
                        token_count=len(chunk_content.split())
                    )
                    
                    chunks.append(doc_chunk)
                
                yield source, document, chunks

        except Exception as e:
            raise ValueError(f"Failed to load document {path}: {str(e)}")