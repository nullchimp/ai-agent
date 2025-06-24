#!/usr/bin/env python3

"""
Test script to verify debug state persistence across API calls.
This will help identify if there's actually an issue with debug state not being persisted.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.debug_capture import get_debug_capture_instance


def test_debug_state_persistence():
    """Test that debug enable/disable state persists across function calls"""
    
    session_id = "test-persistence-session"
    
    # Get initial instance
    capture1 = get_debug_capture_instance(session_id)
    print(f"Initial state - enabled: {capture1.is_enabled()}")
    
    # Enable debug
    capture1.enable()
    print(f"After enable - enabled: {capture1.is_enabled()}")
    
    # Get the same instance again (simulating a new API call)
    capture2 = get_debug_capture_instance(session_id)
    print(f"Second instance - enabled: {capture2.is_enabled()}")
    
    # Verify they are the same instance
    print(f"Same instance: {capture1 is capture2}")
    
    # Disable debug using second instance
    capture2.disable()
    print(f"After disable via second instance - enabled: {capture2.is_enabled()}")
    
    # Check first instance
    print(f"First instance after disable - enabled: {capture1.is_enabled()}")
    
    # Get third instance
    capture3 = get_debug_capture_instance(session_id)
    print(f"Third instance - enabled: {capture3.is_enabled()}")
    
    return capture1.is_enabled() == capture2.is_enabled() == capture3.is_enabled() == False


def test_multiple_sessions():
    """Test that different sessions have independent debug states"""
    
    session1 = "session-1"
    session2 = "session-2"
    
    capture1 = get_debug_capture_instance(session1)
    capture2 = get_debug_capture_instance(session2)
    
    # Enable debug for session1 only
    capture1.enable()
    
    print(f"Session 1 enabled: {capture1.is_enabled()}")
    print(f"Session 2 enabled: {capture2.is_enabled()}")
    
    # Verify they are different instances
    print(f"Different instances: {capture1 is not capture2}")
    
    return capture1.is_enabled() and not capture2.is_enabled()


if __name__ == "__main__":
    print("=== Testing Debug State Persistence ===")
    
    test1_passed = test_debug_state_persistence()
    print(f"Test 1 (State Persistence): {'PASSED' if test1_passed else 'FAILED'}")
    
    print("\n=== Testing Multiple Sessions ===")
    
    test2_passed = test_multiple_sessions()
    print(f"Test 2 (Multiple Sessions): {'PASSED' if test2_passed else 'FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n✅ All tests passed - Debug state persistence is working correctly")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed - Debug state persistence issue detected")
        sys.exit(1)
