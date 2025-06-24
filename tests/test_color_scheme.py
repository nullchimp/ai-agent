#!/usr/bin/env python3
"""
Test script to demonstrate the color scheme functionality in debug_capture.py
"""

import json
from src.core.debug_capture import debug_capture, DebugEventType

def main():
    # Enable debug capture
    debug_capture.enable()
    debug_capture.set_session_id("test_session")
    
    # Test LLM request with colored attributes
    llm_payload = {
        "messages": [
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you!"}
        ],
        "tools": [
            {"name": "search", "description": "Search for information"}
        ],
        "some_large_field": "This is a very long string that should be truncated because it's not in our color scheme" * 10,
        "unimportant_data": {"nested": "data", "that": "should", "be": "truncated"}
    }
    
    debug_capture.capture_llm_request(llm_payload)
    
    # Test tool call with colored attributes  
    debug_capture.capture_tool_call("google_search", {"query": "test search"})
    
    # Test tool result
    debug_capture.capture_tool_result("google_search", {
        "results": ["result1", "result2", "result3"],
        "error": None,
        "metadata": "This should be truncated because it's not important"
    })
    
    # Get all events and display them
    events = debug_capture.get_events()
    
    print("=== Debug Capture Color Scheme Demo ===\n")
    
    for i, event in enumerate(events, 1):
        print(f"Event {i}: {event['event_type']}")
        print(f"Message: {event['message']}")
        print("Data with color scheme:")
        print(json.dumps(event['data'], indent=2))
        print("\n" + "-" * 50 + "\n")
    
    # Demonstrate how frontend can use color information
    print("=== Frontend Color Information ===\n")
    for i, event in enumerate(events, 1):
        data = event['data']
        if '_debug_colors' in data:
            print(f"Event {i} - Colors available:")
            for key, color in data['_debug_colors'].items():
                actual_key = key.replace('_', '').replace('color', '')
                print(f"  - '{actual_key}' should be colored: {color}")
        print()

if __name__ == "__main__":
    main()
