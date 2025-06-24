#!/usr/bin/env python3
"""
Test script to verify session management functionality
"""

import requests
import json
import sys

API_BASE = "http://localhost:5555/api"
headers = {"X-API-Key": "test_12345", "Content-Type": "application/json"}

def test_session_management():
    print("Testing session management functionality...")
    
    # Test 1: Create a new session
    print("\n1. Creating a new session...")
    response = requests.post(f"{API_BASE}/session/new")
    
    if response.status_code == 200:
        session_data = response.json()
        session_id = session_data["session_id"]
        print(f"✅ Session created successfully: {session_id}")
    else:
        print(f"❌ Failed to create session: {response.status_code}")
        return False
    
    # Test 2: List tools for the session
    print(f"\n2. Listing tools for session {session_id}...")
    response = requests.get(f"{API_BASE}/{session_id}/tools", headers=headers)
    
    if response.status_code == 200:
        tools_data = response.json()
        print(f"✅ Retrieved {len(tools_data['tools'])} tools")
        for tool in tools_data['tools']:
            print(f"   - {tool['name']}: {'enabled' if tool['enabled'] else 'disabled'}")
    else:
        print(f"❌ Failed to list tools: {response.status_code}")
        return False
    
    # Test 3: Send a message to the session
    print(f"\n3. Sending a test message to session {session_id}...")
    message = {"query": "Hello, this is a test message"}
    response = requests.post(f"{API_BASE}/{session_id}/ask", headers=headers, json=message)
    
    if response.status_code == 200:
        chat_data = response.json()
        print(f"✅ Received response: {chat_data['response'][:100]}...")
        if chat_data.get('used_tools'):
            print(f"   Tools used: {chat_data['used_tools']}")
    else:
        print(f"❌ Failed to send message: {response.status_code}")
        return False
    
    # Test 4: Toggle a tool
    if tools_data['tools']:
        tool_name = tools_data['tools'][0]['name']
        current_state = tools_data['tools'][0]['enabled']
        new_state = not current_state
        
        print(f"\n4. Toggling tool '{tool_name}' from {current_state} to {new_state}...")
        toggle_data = {"tool_name": tool_name, "enabled": new_state}
        response = requests.post(f"{API_BASE}/{session_id}/tools/toggle", headers=headers, json=toggle_data)
        
        if response.status_code == 200:
            toggle_result = response.json()
            print(f"✅ Tool toggled successfully: {toggle_result['message']}")
        else:
            print(f"❌ Failed to toggle tool: {response.status_code}")
            return False
    
    # Test 5: Delete the session
    print(f"\n5. Deleting session {session_id}...")
    response = requests.delete(f"{API_BASE}/session/{session_id}")
    
    if response.status_code == 204:
        print("✅ Session deleted successfully")
    else:
        print(f"❌ Failed to delete session: {response.status_code}")
        return False
    
    # Test 6: Verify session is deleted (should fail)
    print(f"\n6. Verifying session {session_id} is deleted...")
    response = requests.get(f"{API_BASE}/{session_id}/tools", headers=headers)
    
    if response.status_code == 404 or response.status_code != 200:
        print("✅ Session properly deleted (tools endpoint returns error)")
    else:
        print(f"❌ Session still exists: {response.status_code}")
        return False
    
    print("\n🎉 All session management tests passed!")
    return True

if __name__ == "__main__":
    print("Session Management Test Script")
    print("=" * 40)
    print("Make sure the API server is running on localhost:5555")
    
    try:
        success = test_session_management()
        sys.exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to API server. Is it running on localhost:5555?")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
