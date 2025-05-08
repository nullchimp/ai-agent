from . import Tool

class GoogleSearch(Tool):
	def define(self) -> dict:
		return {
			"type": "function",
			"function": {
				"name": "google_search",
				"description": "Search the web for relevant information.",
				"parameters": {
					"type": "object",
					"properties": {
						"query": {
							"type": "string",
							"description": "The search query to use"
						},
						"num_results": {
							"type": "number",
							"description": "Number of results to return (default: 5, max: 10)"
						}
					},
					"required": ["query"]
				}
			}
		}
    
	def run(self, query: str, num_results: int = 5):

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