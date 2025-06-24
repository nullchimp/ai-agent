#!/usr/bin/env python3
"""
Test script to generate debug events and test the fullscreen functionality
"""

import json
import pytest
from src.core.debug_capture import DebugEventType, get_debug_capture_instance


class TestFullscreen:
    def test_fullscreen_functionality(self):
        # Enable debug capture
        debug_capture = get_debug_capture_instance("fullscreen_test_session")
        debug_capture.enable()
        
        # Generate test events with different types of data
        
        # 1. LLM Request with nested data
        complex_payload = {
            "messages": [
                {"role": "user", "content": "What is the weather like today?"},
                {"role": "assistant", "content": "I'll help you check the weather. Let me search for current weather information."}
            ],
            "tools": [
                {
                    "name": "weather_search",
                    "description": "Search for current weather information",
                    "parameters": {
                        "location": {"type": "string", "description": "Location to search weather for"},
                        "units": {"type": "string", "enum": ["celsius", "fahrenheit"]}
                    }
                }
            ],
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 150,
            "large_context": "This is a very large context field that would normally be truncated in the regular view but should be fully visible in fullscreen mode. " * 20
        }
        
        debug_capture.capture_llm_request(complex_payload)
        
        # 2. Tool call
        debug_capture.capture_tool_call("weather_search", {
            "location": "San Francisco, CA",
            "units": "celsius"
        })
        
        # 3. Tool result with extensive data
        weather_result = {
            "results": {
                "location": "San Francisco, CA",
                "temperature": 18,
                "condition": "Partly cloudy",
                "humidity": 65,
                "wind_speed": 12,
                "forecast": [
                    {"day": "Today", "high": 22, "low": 15, "condition": "Partly cloudy"},
                    {"day": "Tomorrow", "high": 24, "low": 16, "condition": "Sunny"},
                    {"day": "Day after", "high": 21, "low": 14, "condition": "Cloudy"}
                ]
            },
            "metadata": {
                "source": "OpenWeatherMap API",
                "timestamp": "2025-06-24T10:30:00Z",
                "cache_duration": 300,
                "api_version": "2.5"
            },
            "raw_response": {
                "coord": {"lon": -122.4194, "lat": 37.7749},
                "weather": [{"id": 803, "main": "Clouds", "description": "broken clouds", "icon": "04d"}],
                "base": "stations",
                "main": {"temp": 291.15, "feels_like": 290.8, "temp_min": 289.15, "temp_max": 293.15, "pressure": 1013, "humidity": 65},
                "visibility": 10000,
                "wind": {"speed": 3.36, "deg": 250},
                "clouds": {"all": 75},
                "dt": 1719225000,
                "sys": {"type": 2, "id": 2017837, "country": "US", "sunrise": 1719149623, "sunset": 1719202348},
                "timezone": -25200,
                "id": 5391959,
                "name": "San Francisco",
                "cod": 200
            }
        }
        
        debug_capture.capture_tool_result("weather_search", weather_result)
        
        # 4. Error case
        debug_capture.capture_tool_error("invalid_tool", "Tool not found: invalid_tool is not available in the current context")
        
        # 5. MCP call
        debug_capture.capture_mcp_call("file_operations", {
            "operation": "read",
            "path": "/Users/nullchimp/Projects/ai-agent/README.md",
            "encoding": "utf-8"
        })
        
        events = debug_capture.get_events()
        
        print("✅ Debug events generated successfully!")
        print("📊 Total events captured:", len(events))
        print("🌐 Open the web interface and toggle the debug panel to test fullscreen functionality")
        print("🔍 Click the 'Expand' button on any debug event to test fullscreen mode")
        
        # Verify events were captured
        assert len(events) >= 5
        assert any(event['event_type'] == DebugEventType.AGENT_TO_MODEL for event in events)
        assert any(event['event_type'] == DebugEventType.TOOL_CALL for event in events)
        assert any(event['event_type'] == DebugEventType.TOOL_RESULT for event in events)
        assert any(event['event_type'] == DebugEventType.TOOL_ERROR for event in events)
        assert any(event['event_type'] == DebugEventType.MCP_CALL for event in events)
