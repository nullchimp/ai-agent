################################
##            WIP             ##
################################

from typing import List, Generator, Tuple, Optional, Dict, Pattern, Set
import hashlib
import re
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from . import Loader
from core.rag.schema import Document, DocumentChunk, Source


class WebLoader(Loader):
    def __init__(self, 
                url: str, 
                url_pattern: Optional[str] = None, 
                max_urls: int = 10000, 
                chunk_size: int = 1024, 
                chunk_overlap: int = 200):
        
        self.url = url
        self.url_pattern = re.compile(url_pattern) if url_pattern else None
        self.max_urls = max_urls
        self.path = url  # For compatibility with Loader parent class
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        self.visited_urls: Set[str] = set()
        self.found_urls: Set[str] = set()
        
        from llama_index.core.node_parser import SentenceSplitter
        self.sentence_splitter = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

    def create_source(self, source_url) -> Source:
        parsed_url = urlparse(source_url)
        domain = parsed_url.netloc
        
        source = Source(
            name=domain,
            type="website",
            base_uri=source_url
        )
        
        source.id = hashlib.sha256(source_url.encode()).hexdigest()[:16]
        source.add_metadata(**{
            "scheme": parsed_url.scheme,
            "path": parsed_url.path
        })
        
        return source
    
    def _get_urls(self, soup: BeautifulSoup, url: str) -> List[str]:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                              '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            links = []
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                full_url = urljoin(url, href)
                
                # Skip fragment URLs and empty URLs
                if not full_url or "#" in full_url:
                    continue
                    
                # If there's a pattern, only include URLs that match it
                if not full_url.startswith(self.path):
                    continue
                
                links.append(full_url)
                
            return links
            
        except Exception as e:
            raise ValueError(f"Failed to fetch URLs from {url}: {str(e)}")
    
    def _visit_site(self, url: str) -> str:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                              '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            links = self._get_urls(soup, url)

            # Remove script and style tags
            for script in soup(["script", "style"]):
                script.decompose()
                
            # Get text content
            text = soup.get_text(separator=' ', strip=True)
            
            # Remove excess whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            
            return text, links
            
        except Exception as e:
            raise ValueError(f"Failed to fetch content from {url}: {str(e)}")

    def load_data(self) -> Generator[Tuple[Source, Document, List[DocumentChunk]], None, None]:
        try:
            urls_to_process = [self.url]
            
            while urls_to_process:
                current_url = urls_to_process.pop(0)
                display_url = current_url.replace("http://localhost:4000", "https://docs.github.com")

                source = self.create_source(display_url)
                print(f"Processing URL: {current_url}")
                
                # Extract links from the current URL
                content, new_urls = self._visit_site(current_url)
                self.visited_urls.add(current_url)
                # Skip empty content
                if not content:
                    continue

                # Add new unvisited URLs to the processing queue
                for url in new_urls:
                    if not url in self.found_urls:
                        urls_to_process.append(url)
                        self.found_urls.add(url)
                
                print(f"Pending URLs: {len(urls_to_process)}")
                print(f"Content: {content[:100]}...")  # Print first 100 characters of content

                parsed_url = urlparse(current_url)
                title = parsed_url.path.split('/')[-1] or parsed_url.netloc
                
                document = Document(
                    path=display_url,
                    content=content,
                    title=title,
                    source_id=source.id,
                    reference_ids=[hashlib.sha256(url.encode()).hexdigest()[:16] for url in new_urls]
                )
                
                from llama_index.core import Document as LlamaDocument
                llama_doc = LlamaDocument(text=content)
                nodes = self.sentence_splitter.get_nodes_from_documents([llama_doc])
                
                # Create chunk documents
                chunks = []
                for idx, node in enumerate(nodes):
                    chunk_content = node.text
                    
                    doc_chunk = DocumentChunk(
                        path=display_url,
                        content=chunk_content,
                        parent_document_id=document.id,
                        chunk_index=idx,
                        token_count=len(chunk_content.split())
                    )
                    
                    chunks.append(doc_chunk)
                
                yield source, document, chunks
                
        except Exception as e:
            raise ValueError(f"Failed to process URL {self.url}: {str(e)}")