from typing import List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class LoaderConfig:
    path: str
    file_extensions: Optional[List[str]] = None
    uri_replacement: Optional[Tuple[str, str]] = None


@dataclass
class WebLoaderConfig:
    url: str
    uri_replacement: Optional[Tuple[str, str]] = None


DOC_LOADER_CONFIGS = [
    LoaderConfig(
        path="/Users/nullchimp/Projects/customer-security-trust/FAQ",
        file_extensions=['.md'],
        uri_replacement=(
            "/Users/nullchimp/Projects/customer-security-trust/FAQ", 
            "https://github.com/github/customer-security-trust/blob/main/FAQ"
        )
    ),
    LoaderConfig(
        path="/Users/nullchimp/Projects/github-docs/content-copilot",
        file_extensions=['.md']
    )
]

WEB_LOADER_CONFIGS = [
    WebLoaderConfig(
        url="http://localhost:4000/en/enterprise-cloud@latest",
        uri_replacement=(
            "http://localhost:4000", 
            "https://docs.github.com"
        )
    )
]
