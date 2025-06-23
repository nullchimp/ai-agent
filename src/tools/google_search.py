from . import Tool

class GoogleSearch(Tool):
	@property
	def name(self) -> str:
		return "google_search"
	
	@property
	def description(self) -> str:
		return "Perform web searches using Google Custom Search API to retrieve relevant information from the internet. Returns structured search results including titles, URLs, snippets, and metadata. Supports configurable result limits and provides search performance metrics. Requires valid Google API credentials and custom search engine configuration."
	
	@property
	def parameters(self) -> dict:
		return {
			"type": "object",
			"properties": {
				"query": {
					"type": "string",
					"description": "The search query string to submit to Google. Supports standard Google search operators and syntax including quotes for exact phrases, site: for domain filtering, and boolean operators."
				},
				"num_results": {
					"type": "number",
					"description": "Maximum number of search results to return. Valid range is 1-10, defaults to 5 if not specified. Higher values may increase API quota usage and response time."
				}
			},
			"required": ["query"]
		}
    
	async def run(self, query: str, num_results: int = 5):

		from libs.search.service import Service

		service = Service.create()
		results = service.search(query, num_results)
		
		return {
			"query": results.query,
			"total_results": results.total_results,
			"search_time": results.search_time,
			"results": [str(result) for result in results.results],
			"formatted_count": results.formatted_count
		}