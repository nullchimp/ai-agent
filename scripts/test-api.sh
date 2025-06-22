#!/bin/bash

# Check if API_KEY is set
if [ -z "$API_KEY" ]; then
  echo "Error: API_KEY environment variable is not set."
  exit 1
fi

# Test the /api/ask endpoint
curl -X POST http://127.0.0.1:5555/api/ask \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"query": "What is GitHubs policy for handling personal data, especially for users that interact with Claude or Gemini Models in Copilot?"}' \

echo
