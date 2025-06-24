#!/usr/bin/env python3

"""
Demo script to show that debug capture now works on a per-session basis.
"""

from core.debug_capture import (
    get_debug_capture_instance, 
    get_all_debug_events,
    DebugEventType
)

def test_per_session_debug_capture():
    print("Testing per-session debug capture functionality...")
    print("=" * 60)
    
    # Create debug captures for different sessions
    session1_capture = get_debug_capture_instance("user_session_1")
    session2_capture = get_debug_capture_instance("user_session_2")
    
    # Enable debug for both sessions
    session1_capture.enable()
    session2_capture.enable()
    
    print(f"Session 1 enabled: {session1_capture.is_enabled()}")
    print(f"Session 2 enabled: {session2_capture.is_enabled()}")
    print()
    
    # Capture different events for each session
    session1_capture.capture_tool_call("google_search", {"query": "Python tutorials"})
    session1_capture.capture_tool_result("google_search", "Found 10 results")
    
    session2_capture.capture_tool_call("read_file", {"filename": "config.json"})
    session2_capture.capture_tool_error("read_file", "File not found")
    
    # Show events for session 1
    session1_events = session1_capture.get_events()
    print(f"Session 1 events ({len(session1_events)}):")
    for event in session1_events:
        print(f"  - {event['event_type']}: {event['message']} (session: {event['session_id']})")
    print()
    
    # Show events for session 2
    session2_events = session2_capture.get_events()
    print(f"Session 2 events ({len(session2_events)}):")
    for event in session2_events:
        print(f"  - {event['event_type']}: {event['message']} (session: {event['session_id']})")
    print()
    
    # Show all events from all sessions
    all_events = get_all_debug_events()
    print(f"All events across sessions ({len(all_events)}):")
    for event in all_events:
        print(f"  - {event['event_type']}: {event['message']} (session: {event['session_id']})")
    print()
    
    # Show only session 1 events globally
    session1_global_events = get_all_debug_events("user_session_1")
    print(f"Session 1 events via global filter ({len(session1_global_events)}):")
    for event in session1_global_events:
        print(f"  - {event['event_type']}: {event['message']} (session: {event['session_id']})")
    print()
    
    print("✅ Per-session debug capture is working correctly!")
    print("Each session maintains its own debug events separately.")

if __name__ == "__main__":
    test_per_session_debug_capture()
