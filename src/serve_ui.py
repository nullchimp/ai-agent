#!/usr/bin/env python3
"""
Simple HTTP server to serve the ChatGPT-like frontend.
Run this script to serve the UI on http://localhost:8080
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

def serve_ui(port: int = 8080) -> None:
    ui_dir = Path(__file__).parent / "ui"
    
    if not ui_dir.exists():
        print(f"Error: UI directory not found at {ui_dir}")
        sys.exit(1)
    
    os.chdir(ui_dir)
    
    handler = http.server.SimpleHTTPRequestHandler
    
    # Add CORS headers for API calls
    class CORSHTTPRequestHandler(handler):
        def end_headers(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            super().end_headers()
    
    with socketserver.TCPServer(("", port), CORSHTTPRequestHandler) as httpd:
        print(f"Serving UI at http://localhost:{port}")
        print("Press Ctrl+C to stop the server")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

if __name__ == "__main__":
    serve_ui()
