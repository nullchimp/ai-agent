from typing import List, Generator, Tuple
import os
import uuid
import hashlib

from llama_index.core.readers import SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter

from core.rag.schema import Document, DocumentChunk, Source

class WebLoader:
    pass