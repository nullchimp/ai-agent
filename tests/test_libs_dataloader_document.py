import pytest
import os
import hashlib
from unittest.mock import Mock, patch, MagicMock
from typing import List

from src.libs.dataloader.document import DocumentLoader
from src.core.rag.schema import Document, DocumentChunk, Source


class TestDocumentLoader:
    def test_document_loader_create_source(self):
        with patch('os.path.exists', return_value=True):
            loader = DocumentLoader("/test/path")
            source = loader.create_source("/test/path/test_file.txt")
            
            assert isinstance(source, Source)
            assert source.name == "test_file.txt"
            assert source.type == "file"
            assert source.uri == "/test/path/test_file.txt"
            assert source.id == hashlib.sha256("/test/path".encode()).hexdigest()[:16]
            assert source.metadata["file_type"] == "txt"
            assert source.metadata["directory"] == "/test/path"
    
    def test_document_loader_create_source_with_empty_path(self):
        with patch('os.path.exists', return_value=True):
            loader = DocumentLoader("/test/path")
            loader.path = ""
            
            with pytest.raises(ValueError, match="Path cannot be empty."):
                loader.create_source("/test/file.txt")
    
    @pytest.mark.parametrize(
        "file_path,expected_name,expected_type",
        [
            ("/test/data.txt", "data.txt", "txt"),
            ("/nested/path/doc.md", "doc.md", "md"),
            ("/path/with/file.pdf", "file.pdf", "pdf"),
        ]
    )
    def test_document_loader_create_source_variations(self, file_path, expected_name, expected_type):
        with patch('os.path.exists', return_value=True):
            loader = DocumentLoader("/test")
            source = loader.create_source(file_path)
            
            assert source.name == expected_name
            assert source.metadata["file_type"] == expected_type
    
    @patch('src.libs.dataloader.document.SimpleDirectoryReader')
    def test_document_loader_load_data_success(self, mock_reader_class):
        with patch('os.path.exists', return_value=True), \
             patch('os.path.abspath', return_value="/abs/test/path"):
            
            # Create mock documents
            mock_doc1 = MagicMock()
            mock_doc1.text = "Test content 1"
            mock_doc1.metadata = {"file_path": "/abs/test/path/doc1.txt"}
            
            mock_doc2 = MagicMock()
            mock_doc2.text = "Test content 2"
            mock_doc2.metadata = {"file_path": "/abs/test/path/doc2.txt"}
            
            # Set up the reader mock
            mock_reader_instance = MagicMock()
            mock_reader_instance.load_data.return_value = [mock_doc1, mock_doc2]
            mock_reader_class.return_value = mock_reader_instance
            
            # Set up the sentence splitter mock
            loader = DocumentLoader("/test/path")
            mock_nodes1 = [Mock(text="Chunk 1a"), Mock(text="Chunk 1b")]
            mock_nodes2 = [Mock(text="Chunk 2")]
            
            def mock_get_nodes(docs):
                if docs[0] == mock_doc1:
                    return mock_nodes1
                return mock_nodes2
                
            loader.sentence_splitter.get_nodes_from_documents = Mock(side_effect=mock_get_nodes)
            
            # Test the load_data method
            results = list(loader.load_data())
            
            # Assertions
            assert len(results) == 2  # Two documents processed
            
            # First document
            source1, doc1, chunks1 = results[0]
            assert isinstance(source1, Source)
            assert source1.name == "doc1.txt"
            assert doc1.content == "Test content 1"
            assert doc1.title == "doc1.txt"
            assert len(chunks1) == 2
            assert chunks1[0].content == "Chunk 1a"
            assert chunks1[1].content == "Chunk 1b"
            
            # Second document
            source2, doc2, chunks2 = results[1]
            assert isinstance(source2, Source)
            assert source2.name == "doc2.txt"
            assert doc2.content == "Test content 2"
            assert doc2.title == "doc2.txt"
            assert len(chunks2) == 1
            assert chunks2[0].content == "Chunk 2"
    
    @patch('src.libs.dataloader.document.SimpleDirectoryReader')
    def test_document_loader_load_data_empty_doc(self, mock_reader_class):
        with patch('os.path.exists', return_value=True), \
             patch('os.path.abspath', return_value="/abs/test/path"):
            
            # Create mock documents, one with empty text
            mock_doc1 = MagicMock()
            mock_doc1.text = ""  # Empty text
            mock_doc1.metadata = {"file_path": "/abs/test/path/empty_doc.txt"}
            
            mock_doc2 = MagicMock()
            mock_doc2.text = "Test content"
            mock_doc2.metadata = {"file_path": "/abs/test/path/doc.txt"}
            
            # Set up the reader mock
            mock_reader_instance = MagicMock()
            mock_reader_instance.load_data.return_value = [mock_doc1, mock_doc2]
            mock_reader_class.return_value = mock_reader_instance
            
            # Set up the sentence splitter mock
            loader = DocumentLoader("/test/path")
            loader.sentence_splitter.get_nodes_from_documents = Mock(
                return_value=[Mock(text="Chunk")]
            )
            
            # Test the load_data method
            results = list(loader.load_data())
            
            # Assertions - empty document should be skipped
            assert len(results) == 1
            source, doc, chunks = results[0]
            assert doc.title == "doc.txt"
    
    @patch('src.libs.dataloader.document.SimpleDirectoryReader')
    def test_document_loader_load_data_no_docs(self, mock_reader_class):
        with patch('os.path.exists', return_value=True), \
             patch('os.path.abspath', return_value="/abs/test/path"):
            
            # Set up the reader mock to return empty list
            mock_reader_instance = MagicMock()
            mock_reader_instance.load_data.return_value = []
            mock_reader_class.return_value = mock_reader_instance
            
            loader = DocumentLoader("/test/path")
            
            # Test the load_data method
            with pytest.raises(ValueError, match="Failed to load document:"):
                list(loader.load_data())
    
    @patch('src.libs.dataloader.document.SimpleDirectoryReader')
    def test_document_loader_load_data_exception(self, mock_reader_class):
        with patch('os.path.exists', return_value=True), \
             patch('os.path.abspath', return_value="/abs/test/path"):
            
            # Set up the reader mock to raise exception
            mock_reader_instance = MagicMock()
            mock_reader_instance.load_data.side_effect = Exception("Failed to read document")
            mock_reader_class.return_value = mock_reader_instance
            
            loader = DocumentLoader("/test/path")
            
            # Test the load_data method
            with pytest.raises(ValueError, match="Failed to load document.*Failed to read document"):
                list(loader.load_data())
