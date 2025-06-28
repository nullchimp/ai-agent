from . import Tool
from libs.dataloader.web import WebLoader

class WebScraper(Tool):
    @property
    def name(self) -> str:
        return "web_scraper"
    
    @property
    def description(self) -> str:
        return "Extract content from web pages using advanced scraping techniques. Supports JavaScript rendering, element selection, and structured data extraction with rate limiting and caching."
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Target URL to scrape content from. Must be a valid HTTP/HTTPS URL. Supports static pages and JavaScript-rendered content with automatic fallback handling."},
                "max_urls": {"type": "integer", "description": "Maximum recursion for following links from the initial URL. Depth 1 scrapes only the target page, depth 2 scrapes the target page plus one level of linked pages, depth 3 scrapes the target page plus two levels of linked pages, etc. Higher values increase processing time and resource usage. Range: 1-10 (default: 1)"},
            },
            "required": ["url"]
        }
    
    async def run(self, url: str, max_urls: int = 1):
        loader = WebLoader(url, max_urls=max_urls)
        data = []
        for source, doc, chunks in loader.load_data():
            data.append({
                "source": source.uri,
                "content": doc.content
            })
        
        return data

