import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from typing import List, Generator, Tuple

from src.libs.dataloader import Loader
from src.libs.dataloader.document import DocumentLoader
from src.libs.dataloader.web import WebLoader
from src.core.rag.schema import Document, DocumentChunk, Source


class TestLoader:
    def test_loader_init_success(self):
        with patch('os.path.exists', return_value=True):
            loader = Loader("/test/path", recursive=False, chunk_size=512, chunk_overlap=100)
            
            assert loader.path == "/test/path"
            assert loader.recursive is False
            assert loader.chunk_size == 512
            assert loader.chunk_overlap == 100

    def test_loader_init_file_not_found(self):
        with patch('os.path.exists', return_value=False):
            with pytest.raises(ValueError, match="File not found: /nonexistent/path"):
                Loader("/nonexistent/path")

    def test_loader_init_default_params(self):
        with patch('os.path.exists', return_value=True):
            loader = Loader("/test/path")
            
            assert loader.recursive is True
            assert loader.chunk_size == 1024
            assert loader.chunk_overlap == 200

    def test_loader_sentence_splitter_initialization(self):
        with patch('os.path.exists', return_value=True), \
             patch('src.libs.dataloader.SentenceSplitter') as mock_splitter:
            
            loader = Loader("/test/path", chunk_size=512, chunk_overlap=100)
            
            mock_splitter.assert_called_once_with(
                chunk_size=512,
                chunk_overlap=100
            )

    def test_loader_create_source_not_implemented(self):
        with patch('os.path.exists', return_value=True):
            loader = Loader("/test/path")
            
            with pytest.raises(NotImplementedError, match="Subclasses should implement this method"):
                loader.create_source()

    def test_loader_load_data_not_implemented(self):
        with patch('os.path.exists', return_value=True):
            loader = Loader("/test/path")
            
            with pytest.raises(NotImplementedError, match="Subclasses should implement this method"):
                loader.load_data()


class TestDocumentLoader:
    def test_document_loader_inherits_loader(self):
        with patch('os.path.exists', return_value=True):
            loader = DocumentLoader("/test/path")
            assert isinstance(loader, Loader)

    def test_document_loader_create_source_success(self):
        with patch('os.path.exists', return_value=True):
            loader = DocumentLoader("/test/documents/file.txt")
            
            source = loader.create_source("/test/documents/file.txt")
            
            assert isinstance(source, Source)
            assert source.name == "file.txt"
            assert source.type == "file"
            assert source.uri == "/test/documents/file.txt"
            assert source.metadata["file_type"] == "txt"
            assert source.metadata["directory"] == "/test/documents"

    def test_document_loader_create_source_empty_path(self):
        with patch('os.path.exists', return_value=True):
            loader = DocumentLoader("")
            
            with pytest.raises(ValueError, match="Path cannot be empty"):
                loader.create_source("/test/path")

    def test_document_loader_create_source_id_generation(self):
        with patch('os.path.exists', return_value=True):
            loader1 = DocumentLoader("/same/path")
            loader2 = DocumentLoader("/same/path")
            
            source1 = loader1.create_source("/test/file.txt")
            source2 = loader2.create_source("/test/file.txt")
            
            # Same path should generate same ID
            assert source1.id == source2.id

    def test_document_loader_load_data_success(self):
        with patch('os.path.exists', return_value=True), \
             patch('os.path.abspath', return_value="/abs/test/path"), \
             patch('src.libs.dataloader.document.SimpleDirectoryReader') as mock_reader:
            
            # Mock document data
            mock_doc = Mock()
            mock_doc.text = "This is test content for the document."
            mock_doc.metadata = {"file_path": "/abs/test/path/file.txt"}
            
            mock_reader_instance = Mock()
            mock_reader_instance.load_data.return_value = [mock_doc]
            mock_reader.return_value = mock_reader_instance
            
            # Mock sentence splitter
            mock_node1 = Mock()
            mock_node1.text = "This is test content"
            mock_node2 = Mock()
            mock_node2.text = "for the document."
            
            loader = DocumentLoader("/test/path")
            loader.sentence_splitter = Mock()
            loader.sentence_splitter.get_nodes_from_documents.return_value = [mock_node1, mock_node2]
            
            results = list(loader.load_data())
            
            assert len(results) == 1
            source, document, chunks = results[0]
            
            # Check source
            assert isinstance(source, Source)
            assert source.name == "file.txt"
            
            # Check document
            assert isinstance(document, Document)
            assert document.content == "This is test content for the document."
            assert document.title == "file.txt"
            assert document.source_id == source.id
            
            # Check chunks
            assert len(chunks) == 2
            assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)
            assert chunks[0].content == "This is test content"
            assert chunks[1].content == "for the document."
            assert chunks[0].chunk_index == 0
            assert chunks[1].chunk_index == 1

    def test_document_loader_load_data_no_documents(self):
        with patch('os.path.exists', return_value=True), \
             patch('os.path.abspath', return_value="/abs/test/path"), \
             patch('src.libs.dataloader.document.SimpleDirectoryReader') as mock_reader:
            
            mock_reader_instance = Mock()
            mock_reader_instance.load_data.return_value = []
            mock_reader.return_value = mock_reader_instance
            
            loader = DocumentLoader("/test/path")
            
            with pytest.raises(ValueError, match="Failed to load document: /abs/test/path"):
                list(loader.load_data())

    def test_document_loader_load_data_empty_document(self):
        with patch('os.path.exists', return_value=True), \
             patch('os.path.abspath', return_value="/abs/test/path"), \
             patch('src.libs.dataloader.document.SimpleDirectoryReader') as mock_reader:
            
            # Mock document with empty text
            mock_doc = Mock()
            mock_doc.text = ""
            mock_doc.metadata = {"file_path": "/abs/test/path/file.txt"}
            
            mock_reader_instance = Mock()
            mock_reader_instance.load_data.return_value = [mock_doc]
            mock_reader.return_value = mock_reader_instance
            
            loader = DocumentLoader("/test/path")
            
            results = list(loader.load_data())
            
            # Should skip empty documents
            assert len(results) == 0

    def test_document_loader_load_data_multiple_documents(self):
        with patch('os.path.exists', return_value=True), \
             patch('os.path.abspath', return_value="/abs/test/path"), \
             patch('src.libs.dataloader.document.SimpleDirectoryReader') as mock_reader:
            
            # Mock multiple documents
            mock_doc1 = Mock()
            mock_doc1.text = "First document content"
            mock_doc1.metadata = {"file_path": "/abs/test/path/file1.txt"}
            
            mock_doc2 = Mock()
            mock_doc2.text = "Second document content"
            mock_doc2.metadata = {"file_path": "/abs/test/path/file2.txt"}
            
            mock_reader_instance = Mock()
            mock_reader_instance.load_data.return_value = [mock_doc1, mock_doc2]
            mock_reader.return_value = mock_reader_instance
            
            # Mock sentence splitter
            mock_node = Mock()
            mock_node.text = "content"
            
            loader = DocumentLoader("/test/path")
            loader.sentence_splitter = Mock()
            loader.sentence_splitter.get_nodes_from_documents.return_value = [mock_node]
            
            results = list(loader.load_data())
            
            assert len(results) == 2

    def test_document_loader_load_data_exception_handling(self):
        with patch('os.path.exists', return_value=True), \
             patch('os.path.abspath', return_value="/abs/test/path"), \
             patch('src.libs.dataloader.document.SimpleDirectoryReader') as mock_reader:
            
            mock_reader.side_effect = Exception("Reader failed")
            
            loader = DocumentLoader("/test/path")
            
            with pytest.raises(ValueError, match="Failed to load document /abs/test/path: Reader failed"):
                list(loader.load_data())

    def test_document_loader_reader_configuration(self):
        with patch('os.path.exists', return_value=True), \
             patch('os.path.abspath', return_value="/abs/test/path"), \
             patch('src.libs.dataloader.document.SimpleDirectoryReader') as mock_reader:
            
            mock_reader_instance = Mock()
            mock_reader_instance.load_data.return_value = []
            mock_reader.return_value = mock_reader_instance
            
            loader = DocumentLoader("/test/path", recursive=False)
            
            try:
                list(loader.load_data())
            except ValueError:
                pass  # Expected since no documents
            
            # Check that SimpleDirectoryReader was called with correct parameters
            mock_reader.assert_called_once_with(
                input_dir="/abs/test/path",
                filename_as_id=True,
                recursive=False
            )


class TestWebLoader:
    def test_web_loader_init(self):
        loader = WebLoader(
            url="https://example.com",
            url_pattern=".*example.*",
            max_urls=100,
            chunk_size=512,
            chunk_overlap=100
        )
        
        assert loader.url == "https://example.com"
        assert loader.path == "https://example.com"
        assert loader.max_urls == 100
        assert loader.chunk_size == 512
        assert loader.chunk_overlap == 100
        assert loader.url_pattern is not None
        assert isinstance(loader.visited_urls, set)
        assert isinstance(loader.found_urls, set)

    def test_web_loader_init_defaults(self):
        loader = WebLoader("https://example.com")
        
        assert loader.url_pattern is None
        assert loader.max_urls == 10000
        assert loader.chunk_size == 1024
        assert loader.chunk_overlap == 200

    def test_web_loader_sentence_splitter_initialization(self):
        with patch('src.libs.dataloader.web.SentenceSplitter') as mock_splitter:
            loader = WebLoader("https://example.com", chunk_size=512, chunk_overlap=100)
            
            mock_splitter.assert_called_once_with(
                chunk_size=512,
                chunk_overlap=100
            )

    def test_web_loader_create_source(self):
        loader = WebLoader("https://example.com")
        source = loader.create_source("https://example.com/page")
        
        assert isinstance(source, Source)
        assert source.name == "example.com"
        assert source.type == "website"
        assert source.uri == "https://example.com/page"
        assert source.metadata["scheme"] == "https"
        assert source.metadata["path"] == "/page"

    def test_web_loader_create_source_complex_url(self):
        loader = WebLoader("https://example.com")
        source = loader.create_source("https://subdomain.example.com/path/to/page?param=value")
        
        assert source.name == "subdomain.example.com"
        assert source.metadata["scheme"] == "https"
        assert source.metadata["path"] == "/path/to/page"

    def test_web_loader_get_urls_success(self):
        loader = WebLoader("https://example.com")
        
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = '''
        <html>
            <body>
                <a href="/page1">Page 1</a>
                <a href="https://example.com/page2">Page 2</a>
                <a href="https://other.com/page3">Other Page</a>
                <a href="#fragment">Fragment</a>
            </body>
        </html>
        '''
        
        with patch('src.libs.dataloader.web.requests.get', return_value=mock_response), \
             patch('src.libs.dataloader.web.BeautifulSoup') as mock_soup:
            
            mock_soup_instance = Mock()
            mock_a_tags = [
                Mock(**{'get.return_value': '/page1', '__getitem__': lambda self, key: '/page1'}),
                Mock(**{'get.return_value': 'https://example.com/page2', '__getitem__': lambda self, key: 'https://example.com/page2'}),
                Mock(**{'get.return_value': 'https://other.com/page3', '__getitem__': lambda self, key: 'https://other.com/page3'}),
                Mock(**{'get.return_value': '#fragment', '__getitem__': lambda self, key: '#fragment'})
            ]
            
            for tag in mock_a_tags:
                tag.__getitem__ = Mock(side_effect=lambda key: tag.get.return_value)
            
            mock_soup_instance.find_all.return_value = mock_a_tags
            mock_soup.return_value = mock_soup_instance
            
            soup = Mock()  # Dummy soup parameter
            urls = loader._get_urls(soup, "https://example.com")
            
            # Should only include URLs that start with the base path and don't have fragments
            expected_urls = ["https://example.com/page1", "https://example.com/page2"]
            assert set(urls) == set(expected_urls)

    def test_web_loader_get_urls_request_error(self):
        loader = WebLoader("https://example.com")
        
        with patch('src.libs.dataloader.web.requests.get', side_effect=Exception("Network error")):
            soup = Mock()
            
            with pytest.raises(ValueError, match="Failed to fetch URLs from https://example.com: Network error"):
                loader._get_urls(soup, "https://example.com")

    def test_web_loader_visit_site_success(self):
        loader = WebLoader("https://example.com")
        
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = "<html><body><h1>Title</h1><p>Content</p></body></html>"
        
        with patch('src.libs.dataloader.web.requests.get', return_value=mock_response), \
             patch('src.libs.dataloader.web.BeautifulSoup') as mock_soup:
            
            mock_soup_instance = Mock()
            mock_soup.return_value = mock_soup_instance
            
            result = loader._visit_site("https://example.com")
            
            # Should return the soup instance
            assert result == mock_soup_instance

    def test_web_loader_visit_site_request_error(self):
        loader = WebLoader("https://example.com")
        
        with patch('src.libs.dataloader.web.requests.get', side_effect=Exception("Connection failed")):
            with pytest.raises(Exception, match="Connection failed"):
                loader._visit_site("https://example.com")

    def test_web_loader_request_headers(self):
        loader = WebLoader("https://example.com")
        
        with patch('src.libs.dataloader.web.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.text = "<html></html>"
            mock_get.return_value = mock_response
            
            with patch('src.libs.dataloader.web.BeautifulSoup'):
                loader._visit_site("https://example.com")
            
            # Check that proper headers were used
            call_args = mock_get.call_args
            headers = call_args[1]['headers']
            assert 'User-Agent' in headers
            assert 'Mozilla' in headers['User-Agent']
            assert call_args[1]['timeout'] == 30


class TestLoaderIntegration:
    def test_document_loader_integration(self):
        """Test complete document loading workflow"""
        with patch('os.path.exists', return_value=True), \
             patch('os.path.abspath', return_value="/abs/test/path"), \
             patch('src.libs.dataloader.document.SimpleDirectoryReader') as mock_reader:
            
            # Mock complete workflow
            mock_doc = Mock()
            mock_doc.text = "This is a test document with multiple sentences. It should be split into chunks."
            mock_doc.metadata = {"file_path": "/abs/test/path/document.md"}
            
            mock_reader_instance = Mock()
            mock_reader_instance.load_data.return_value = [mock_doc]
            mock_reader.return_value = mock_reader_instance
            
            # Mock sentence splitter with realistic behavior
            mock_node1 = Mock()
            mock_node1.text = "This is a test document with multiple sentences."
            mock_node2 = Mock()
            mock_node2.text = "It should be split into chunks."
            
            loader = DocumentLoader("/test/path", chunk_size=50, chunk_overlap=10)
            loader.sentence_splitter = Mock()
            loader.sentence_splitter.get_nodes_from_documents.return_value = [mock_node1, mock_node2]
            
            results = list(loader.load_data())
            source, document, chunks = results[0]
            
            # Verify complete data structure
            assert source.type == "file"
            assert source.metadata["file_type"] == "md"
            assert document.source_id == source.id
            assert len(chunks) == 2
            assert all(chunk.parent_id == document.id for chunk in chunks)
            assert chunks[0].chunk_index == 0
            assert chunks[1].chunk_index == 1

    def test_web_loader_url_filtering(self):
        """Test URL filtering logic"""
        loader = WebLoader("https://example.com/blog")
        
        # Test various URL scenarios
        test_urls = [
            "https://example.com/blog/post1",      # Should include
            "https://example.com/blog/post2",      # Should include  
            "https://other.com/blog/post",         # Should exclude
            "https://example.com/other/page",      # Should exclude
            "https://example.com/blog#fragment",   # Should exclude (has fragment)
            "",                                    # Should exclude (empty)
        ]
        
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = "<html></html>"
        
        with patch('src.libs.dataloader.web.requests.get', return_value=mock_response), \
             patch('src.libs.dataloader.web.BeautifulSoup') as mock_soup:
            
            mock_soup_instance = Mock()
            mock_a_tags = []
            
            for url in test_urls:
                tag = Mock()
                tag.__getitem__ = Mock(return_value=url)
                tag.get = Mock(return_value=url)
                mock_a_tags.append(tag)
            
            mock_soup_instance.find_all.return_value = mock_a_tags
            mock_soup.return_value = mock_soup_instance
            
            soup = Mock()
            urls = loader._get_urls(soup, "https://example.com/blog")
            
            # Should only include URLs under the base path without fragments
            expected = ["https://example.com/blog/post1", "https://example.com/blog/post2"]
            assert set(urls) == set(expected)
