import pytest
import hashlib
import re
from unittest.mock import Mock, patch, MagicMock
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from src.libs.dataloader.web import WebLoader
from src.core.rag.schema import Source


class TestWebLoader:
    def test_web_loader_init(self):
        url = "https://example.com"
        url_pattern = ".*example\\.com.*"
        max_urls = 50
        chunk_size = 500
        chunk_overlap = 100
        
        loader = WebLoader(
            url=url,
            url_pattern=url_pattern,
            max_urls=max_urls,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        assert loader.url == url
        assert loader.path == url  # path is set to url for compatibility
        assert isinstance(loader.url_pattern, re.Pattern)
        assert loader.max_urls == max_urls
        assert loader.chunk_size == chunk_size
        assert loader.chunk_overlap == chunk_overlap
        assert loader.visited_urls == set()
        assert loader.found_urls == set()
    
    def test_web_loader_init_default_values(self):
        url = "https://example.com"
        
        loader = WebLoader(url)
        
        assert loader.url == url
        assert loader.url_pattern is None
        assert loader.max_urls == 10000
        assert loader.chunk_size == 1024
        assert loader.chunk_overlap == 200
        
        # Check that sentence splitter was initialized with correct params
        with patch('src.libs.dataloader.web.SentenceSplitter') as mock_splitter:
            loader = WebLoader("https://example.com")
            
            mock_splitter.assert_called_once_with(
                chunk_size=1024,
                chunk_overlap=200
            )
    
    def test_web_loader_create_source(self):
        url = "https://example.com/path/page.html?param=value"
        loader = WebLoader(url)
        
        source = loader.create_source(url)
        
        assert isinstance(source, Source)
        assert source.name == "example.com"
        assert source.type == "website"
        assert source.uri == url
        assert source.id == hashlib.sha256(url.encode()).hexdigest()[:16]
        assert source.metadata["scheme"] == "https"
        assert source.metadata["path"] == "/path/page.html"
    
    def test_get_urls_basic(self):
        with patch('src.libs.dataloader.web.requests.get') as mock_get, \
             patch('src.libs.dataloader.web.BeautifulSoup') as mock_soup_class:
            
            # Setup mocks
            mock_response = MagicMock()
            mock_response.text = "<html><body></body></html>"
            mock_get.return_value = mock_response
            
            mock_soup = MagicMock()
            mock_soup_class.return_value = mock_soup
            
            # Setup mock a tags
            mock_a1 = {"href": "/page1.html"}
            mock_a2 = {"href": "/page2.html"}
            mock_a3 = {"href": "https://example.com/page3.html"}
            
            mock_soup.find_all.return_value = [
                MagicMock(**{"__getitem__": lambda self, key: mock_a1.get(key)}),
                MagicMock(**{"__getitem__": lambda self, key: mock_a2.get(key)}),
                MagicMock(**{"__getitem__": lambda self, key: mock_a3.get(key)})
            ]
            
            # Call the method
            loader = WebLoader("https://example.com")
            urls = loader._get_urls(mock_soup, "https://example.com")
            
            # Assertions
            assert len(urls) == 0  # All URLs are handled by the soup returned links
            mock_get.assert_called_once()
            assert "User-Agent" in mock_get.call_args.kwargs["headers"]
            mock_soup_class.assert_called_once_with(mock_response.text, 'html.parser')
    
    def test_get_urls_with_error(self):
        with patch('src.libs.dataloader.web.requests.get') as mock_get:
            mock_get.side_effect = Exception("Connection timeout")
            
            loader = WebLoader("https://example.com")
            
            with pytest.raises(ValueError, match="Failed to fetch URLs from.*Connection timeout"):
                loader._get_urls(None, "https://example.com")
    
    def test_visit_site_success(self):
        with patch('src.libs.dataloader.web.requests.get') as mock_get, \
             patch('src.libs.dataloader.web.BeautifulSoup') as mock_soup_class:
            
            # Setup mocks
            mock_response = MagicMock()
            mock_response.text = "<html><body><p>Content</p></body></html>"
            mock_get.return_value = mock_response
            
            mock_soup = MagicMock()
            mock_soup_class.return_value = mock_soup
            
            # Call the method
            loader = WebLoader("https://example.com")
            loader._visit_site("https://example.com/page")
            
            # Assertions
            mock_get.assert_called_once()
            assert "User-Agent" in mock_get.call_args.kwargs["headers"]
            mock_soup_class.assert_called_once_with(mock_response.text, 'html.parser')
