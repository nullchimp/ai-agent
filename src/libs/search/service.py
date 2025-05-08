"""
Google search functionality service module.
"""
import os
from .client import Client, GoogleClient, SearchResults


class Service:
    """Service that provides high-level search operations."""
    
    def __init__(self, client: Client):
        self.client = client
    
    @classmethod
    def create(cls) -> 'Service':
        api_key = os.environ.get("GOOGLE_API_KEY")
        search_engine_id = os.environ.get("GOOGLE_SEARCH_ENGINE_ID")
        
        if not api_key or not search_engine_id:
            raise ValueError(
                "Missing required environment variables: "
                "GOOGLE_API_KEY and GOOGLE_SEARCH_ENGINE_ID"
            )
        
        client = GoogleClient(
            api_key=api_key,
            search_cx=search_engine_id
        )
        
        return cls(client)
    
    def search(self, query: str, num_results: int = 10) -> SearchResults:
        if self.client is None:
            raise ValueError("Search client not configured")
        
        return self.client.search(query, num_results)