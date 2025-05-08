"""
Google search functionality client module.
"""
from dataclasses import dataclass
from typing import List, Optional, Protocol
import googleapiclient.discovery


@dataclass
class SearchResult:
    """Represents a single search result."""
    title: str
    link: str
    snippet: str
    display_link: str
    source: str


@dataclass
class SearchResults:
    """Contains a collection of search results."""
    query: str
    total_results: int
    search_time: float
    results: List[SearchResult]
    formatted_count: str


class Client(Protocol):
    """Protocol for search operations."""
    
    def search(self, query: str, num_results: int) -> SearchResults:
        """
        Performs a search with the given query.
        
        Args:
            query: The search query
            num_results: The number of results to return
            
        Returns:
            SearchResults object containing the search results
        """
        ...


class GoogleClient:
    """Implements the Client interface using Google Custom Search API."""
    
    def __init__(self, api_key: str, search_cx: str, source_name: str = "Google"):
        """
        Initialize a new Google search client.
        
        Args:
            api_key: Google API key
            search_cx: Custom Search Engine ID
            source_name: Source name for search results
            
        Raises:
            ValueError: If API key or search engine ID are missing
        """
        if not api_key:
            raise ValueError("Google API key is required")
        
        if not search_cx:
            raise ValueError("Search engine ID (cx) is required")
        
        self.service = googleapiclient.discovery.build(
            "customsearch", "v1", 
            developerKey=api_key
        )
        self.search_cx = search_cx
        self.source_name = source_name
    
    def search(self, query: str, num_results: int) -> SearchResults:
        """
        Performs a Google search with the given query.
        
        Args:
            query: The search query
            num_results: The number of results to return
            
        Returns:
            SearchResults object containing the search results
            
        Raises:
            ValueError: If the search query is empty
        """
        if not query:
            raise ValueError("Search query cannot be empty")
        
        if num_results <= 0:
            num_results = 10  # Default to 10 results
        elif num_results > 10:
            num_results = 10  # Google CSE free tier restricts to 10 results
        
        # Perform the search
        search_request = self.service.cse().list(
            q=query,
            cx=self.search_cx,
            num=num_results
        )
        response = search_request.execute()
        
        # Extract search information
        search_info = response.get("searchInformation", {})
        total_results = int(search_info.get("totalResults", "0"))
        search_time = float(search_info.get("searchTime", 0.0))
        formatted_count = search_info.get("formattedTotalResults", "0")
        
        # Parse search results
        items = response.get("items", [])
        results = []
        
        for item in items:
            results.append(SearchResult(
                title=item.get("title", ""),
                link=item.get("link", ""),
                snippet=item.get("snippet", ""),
                display_link=item.get("displayLink", ""),
                source=self.source_name
            ))
        
        return SearchResults(
            query=query,
            total_results=total_results,
            search_time=search_time,
            results=results,
            formatted_count=formatted_count
        )