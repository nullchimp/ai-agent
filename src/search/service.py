"""
Google search functionality service module.
"""
import os
from typing import Optional

from src.search.client import Client, GoogleClient, SearchResults


class Service:
    """Service that provides high-level search operations."""
    
    def __init__(self, client: Client):
        """
        Initialize a Search Service with the provided client.
        
        Args:
            client: A client implementing the Client protocol
        """
        self.client = client
    
    @classmethod
    def create(cls) -> 'Service':
        """
        Creates a new Service with a Google client initialized from env vars.
        
        Returns:
            A new Service instance
            
        Raises:
            ValueError: If required environment variables are missing
        """
        # Get required API credentials from environment
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
        """
        Performs a search with the configured client.
        
        Args:
            query: The search query
            num_results: The number of results to return
            
        Returns:
            SearchResults object containing the search results
            
        Raises:
            ValueError: If the search client is not configured
        """
        if self.client is None:
            raise ValueError("Search client not configured")
        
        return self.client.search(query, num_results)