#!/usr/bin/env python3
"""
Test to verify frontend session functionality by inspecting localStorage
and network requests when the browser loads the chat interface.
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import json
import sys

def setup_driver():
    """Setup Chrome driver with necessary options"""
    options = Options()
    options.add_argument('--headless')  # Run in headless mode
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    
    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        print(f"❌ Failed to setup Chrome driver: {e}")
        print("Please ensure ChromeDriver is installed and in PATH")
        return None

def test_frontend_session_storage():
    """Test that frontend properly stores sessionId in localStorage"""
    print("Testing frontend session storage functionality...")
    
    driver = setup_driver()
    if not driver:
        return False
    
    try:
        # Load the chat interface
        file_path = "file:///Users/nullchimp/Projects/ai-agent/src/ui/index.html"
        print(f"Loading chat interface: {file_path}")
        driver.get(file_path)
        
        # Wait for the page to load
        WebDriverWait(driver, 10).wait(
            EC.presence_of_element_located((By.ID, "messagesContainer"))
        )
        
        # Wait a bit for JavaScript to initialize
        time.sleep(2)
        
        # Check localStorage for chat sessions
        local_storage_data = driver.execute_script("return localStorage.getItem('chatSessions');")
        
        if local_storage_data:
            try:
                sessions = json.loads(local_storage_data)
                print(f"✅ Found {len(sessions)} sessions in localStorage")
                
                # Check each session for sessionId
                for i, session in enumerate(sessions):
                    if 'sessionId' in session:
                        print(f"✅ Session {i+1} has sessionId: {session['sessionId']}")
                    else:
                        print(f"⚠️  Session {i+1} missing sessionId (legacy session)")
                        
                return True
            except json.JSONDecodeError:
                print("❌ Invalid JSON in localStorage")
                return False
        else:
            print("ℹ️  No existing sessions in localStorage (fresh installation)")
            return True
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False
    finally:
        driver.quit()

def test_api_endpoints_available():
    """Test that the API endpoints are available"""
    import requests
    
    print("\nTesting API endpoints availability...")
    
    api_base = "http://localhost:5555/api"
    
    try:
        # Test session creation endpoint
        response = requests.post(f"{api_base}/session/new", timeout=5)
        if response.status_code == 200:
            session_data = response.json()
            session_id = session_data["session_id"]
            print(f"✅ Session creation endpoint working: {session_id}")
            
            # Test session-based endpoints
            headers = {"X-API-Key": "test_12345"}
            
            # Test tools endpoint
            tools_response = requests.get(f"{api_base}/{session_id}/tools", headers=headers, timeout=5)
            if tools_response.status_code == 200:
                print("✅ Tools endpoint working")
            else:
                print(f"❌ Tools endpoint failed: {tools_response.status_code}")
                
            # Test debug endpoint
            debug_response = requests.get(f"{api_base}/{session_id}/debug", headers=headers, timeout=5)
            if debug_response.status_code == 200:
                print("✅ Debug endpoint working")
            else:
                print(f"❌ Debug endpoint failed: {debug_response.status_code}")
                
            # Test session deletion
            delete_response = requests.delete(f"{api_base}/session/{session_id}", timeout=5)
            if delete_response.status_code == 204:
                print("✅ Session deletion endpoint working")
            else:
                print(f"❌ Session deletion failed: {delete_response.status_code}")
                
            return True
        else:
            print(f"❌ Session creation failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API server not available: {e}")
        print("Make sure to start the API server with: python src/main.py --api")
        return False

def main():
    print("Frontend Session Integration Test")
    print("=" * 50)
    
    # Test API endpoints first
    api_test = test_api_endpoints_available()
    
    # Test frontend localStorage (if Selenium is available)
    try:
        frontend_test = test_frontend_session_storage()
    except ImportError:
        print("\n⚠️  Selenium not available - skipping frontend localStorage test")
        print("Install with: pip install selenium")
        frontend_test = True  # Don't fail the test if Selenium isn't available
    
    if api_test and frontend_test:
        print("\n✅ All session integration tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
