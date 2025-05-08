from dotenv import load_dotenv
load_dotenv()

from libs.azureopenai.chat import Chat
from libs.search.service import Service
from libs.fileops.file import FileService
from libs.webfetch.service import WebMarkdownService

chat = Chat.create()
system_role = "You are a helpful assistant."
user_prompt = "What is the capital of France?"

response = chat.send_prompt(system_role, user_prompt)
print(response)

search = Service.create()
query = "What is the capital of France?"
num_results = 5

search_results = search.search(query, num_results)
for result in search_results.results:
    print(result)
    print("/n")

file_service = FileService("docs")
file_path = "example.txt"
content = "This is an example content."
file_service.write_to_file(file_path, content)
print(f"File written to {file_path}")

read_content = file_service.read_file(file_path)
print(f"Read content: {read_content}")

files = file_service.list_files()
print(f"Files in 'docs' directory: {files}")

# Example of using the new WebMarkdownService to fetch a web page and convert it to Markdown
web_markdown_service = WebMarkdownService.create()
url = "https://home.adelphi.edu/~ca19535/page%204.html"
try:
    markdown_content, status_code = web_markdown_service.fetch_as_markdown(url)
    print(f"Fetched content from {url} with status code {status_code}")
    print("First 5000 characters of Markdown content:")
    print(markdown_content[:5000] + "...")
except Exception as e:
    print(f"Error fetching content from {url}: {e}")