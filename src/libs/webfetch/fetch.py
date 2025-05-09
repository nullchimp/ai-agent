
import requests
from typing import Optional, Dict, Any, Tuple


class WebFetcher:
    

    @staticmethod
    def create() -> "WebFetcher":
        return WebFetcher()

    def fetch_content(self, url: str, headers: Optional[Dict[str, str]] = None) -> Tuple[str, int]:
        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        if headers:
            default_headers.update(headers)
            
        try:
            response = requests.get(url, headers=default_headers, timeout=30)
            response.raise_for_status()
            return response.text, response.status_code
        except requests.RequestException as e:
            raise e