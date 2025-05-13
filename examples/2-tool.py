from utils import pretty_print
from libs.search.service import Service

service = Service.create()
query = "Current chancellor of Germany?"
pretty_print("Query", query)

results = service.search(query, 5)
pretty_print("Results", results)

### FUNC
# {
#    "type": "function",
#    "function": {
#         "name": "google_search",
#         "description": "Search the web for relevant information.",
#         "parameters": {
#             "type": "object",
#             "properties": {
#                 "query": {
#                     "type": "string",
#                     "description": "The search query to use"
#                 },
#                 "num_results": {
#                     "type": "number",
#                     "description": "Number of results to return (default: 5, max: 10)"
#                 }
#             },
#             "required": ["query"]
#         }
#     }
# }