from . import Tool
from typing import Dict, Optional

class WebFetch(Tool):
    def define(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": f"{self.name}",
                "description": "Fetch a web page and convert it to Markdown format.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The URL of the webpage to fetch"
                        },
                        "headers": {
                            "type": "object",
                            "description": "Optional HTTP headers for the request",
                            "additionalProperties": {
                                "type": "string"
                            }
                        }
                    },
                    "required": ["url"]
                }
            }
        }
    
    async def run(self, url: str, headers: Optional[Dict[str, str]] = None):
        from libs.webfetch.service import WebMarkdownService
        
        service = WebMarkdownService.create()
        markdown_content, status_code = service.fetch_as_markdown(url, headers)
        
        return {
            "url": url,
            "status_code": status_code,
            "markdown_content": markdown_content
        }