#!/usr/bin/env python3

"""
Test script to verify debug state persistence through the actual API endpoints.
"""

import sys
import os
import requests
import json
import uuid

# Test configuration
BASE_URL = "http://localhost:8000"
API_KEY = "test_12345"

def make_request(method, endpoint, data=None, headers=None):
    """Make HTTP request with proper error handling"""
    if headers is None:
        headers = {"X-API-Key": API_KEY}
    
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        return response
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API server. Please start the server first.")
        print("Run: uvicorn src.api.app:app --reload")
        sys.exit(1)

def test_debug_api_persistence():
    """Test debug state persistence through API endpoints"""
    
    print("Creating new session...")
    # Create new session
    response = make_request("POST", "/api/session/new", headers={})
    if response.status_code != 200:
        print(f"❌ Failed to create session: {response.status_code} - {response.text}")
        return False
    
    session_data = response.json()
    session_id = session_data["session_id"]
    print(f"✅ Created session: {session_id}")
    
    # Check initial debug state
    response = make_request("GET", f"/api/{session_id}/debug")
    if response.status_code != 200:
        print(f"❌ Failed to get debug info: {response.status_code} - {response.text}")
        return False
    
    debug_data = response.json()
    initial_enabled = debug_data["enabled"]
    print(f"Initial debug state: {initial_enabled}")
    
    # Enable debug
    response = make_request("POST", f"/api/{session_id}/debug/toggle", {"enabled": True})
    if response.status_code != 200:
        print(f"❌ Failed to enable debug: {response.status_code} - {response.text}")
        return False
    
    toggle_data = response.json()
    enabled_after_toggle = toggle_data["enabled"]
    print(f"Debug state after enable: {enabled_after_toggle}")
    
    # Check debug state again
    response = make_request("GET", f"/api/{session_id}/debug")
    if response.status_code != 200:
        print(f"❌ Failed to get debug info after enable: {response.status_code} - {response.text}")
        return False
    
    debug_data = response.json()
    enabled_after_get = debug_data["enabled"]
    print(f"Debug state on subsequent GET: {enabled_after_get}")
    
    # Disable debug
    response = make_request("POST", f"/api/{session_id}/debug/toggle", {"enabled": False})
    if response.status_code != 200:
        print(f"❌ Failed to disable debug: {response.status_code} - {response.text}")
        return False
    
    toggle_data = response.json()
    disabled_after_toggle = toggle_data["enabled"]
    print(f"Debug state after disable: {disabled_after_toggle}")
    
    # Final check
    response = make_request("GET", f"/api/{session_id}/debug")
    if response.status_code != 200:
        print(f"❌ Failed to get debug info after disable: {response.status_code} - {response.text}")
        return False
    
    debug_data = response.json()
    disabled_after_get = debug_data["enabled"]
    print(f"Debug state on final GET: {disabled_after_get}")
    
    # Clean up
    response = make_request("DELETE", f"/api/session/{session_id}", headers={})
    if response.status_code == 204:
        print(f"✅ Cleaned up session: {session_id}")
    
    # Verify the sequence
    expected_sequence = [False, True, True, False, False]  # initial, after_enable, get_after_enable, after_disable, final_get
    actual_sequence = [initial_enabled, enabled_after_toggle, enabled_after_get, disabled_after_toggle, disabled_after_get]
    
    print(f"Expected sequence: {expected_sequence}")
    print(f"Actual sequence:   {actual_sequence}")
    
    return expected_sequence == actual_sequence

def test_multiple_sessions_api():
    """Test that multiple sessions have independent debug states"""
    
    print("\nTesting multiple sessions...")
    
    # Create two sessions
    response1 = make_request("POST", "/api/session/new", headers={})
    response2 = make_request("POST", "/api/session/new", headers={})
    
    if response1.status_code != 200 or response2.status_code != 200:
        print("❌ Failed to create sessions")
        return False
    
    session1 = response1.json()["session_id"]
    session2 = response2.json()["session_id"]
    print(f"✅ Created sessions: {session1}, {session2}")
    
    # Enable debug for session1 only
    response = make_request("POST", f"/api/{session1}/debug/toggle", {"enabled": True})
    if response.status_code != 200:
        print("❌ Failed to enable debug for session1")
        return False
    
    # Check both sessions
    response1 = make_request("GET", f"/api/{session1}/debug")
    response2 = make_request("GET", f"/api/{session2}/debug")
    
    if response1.status_code != 200 or response2.status_code != 200:
        print("❌ Failed to get debug states")
        return False
    
    session1_enabled = response1.json()["enabled"]
    session2_enabled = response2.json()["enabled"]
    
    print(f"Session1 debug: {session1_enabled}")
    print(f"Session2 debug: {session2_enabled}")
    
    # Clean up
    make_request("DELETE", f"/api/session/{session1}", headers={})
    make_request("DELETE", f"/api/session/{session2}", headers={})
    
    return session1_enabled and not session2_enabled

if __name__ == "__main__":
    print("=== Testing Debug State Persistence via API ===")
    
    test1_passed = test_debug_api_persistence()
    print(f"Test 1 (API State Persistence): {'PASSED' if test1_passed else 'FAILED'}")
    
    test2_passed = test_multiple_sessions_api()
    print(f"Test 2 (Multiple Sessions API): {'PASSED' if test2_passed else 'FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n✅ All API tests passed - Debug state persistence works correctly via API")
        sys.exit(0)
    else:
        print("\n❌ Some API tests failed - Debug state persistence issue detected in API")
        sys.exit(1)
